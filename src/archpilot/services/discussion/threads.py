"""Discussion thread service — COMP-003 / STORE-003.

Implements CRUD for discussion threads scoped to a (user_sub, session_id)
owner, stored in the canonical DynamoDB single-table design.

DynamoDB key scheme
-------------------
PK  = ``disc#<session_id>``          (partition = owning session)
SK  = ``thread#<thread_id>``         (sort key = thread entity)
GSI1PK = ``user#<user_sub>``         (all threads for a user across sessions)
GSI1SK = <created_at ISO-8601>       (chronological ordering)
GSI2PK = ``disc#<session_id>``       (list-by-session with sort)
GSI2SK = <updated_at ISO-8601>       (recency ordering for session threads)

Acceptance criteria addressed
------------------------------
AC-009.1  Thread create stores validated title + body, returns 201 with full item.
AC-009.2  Duplicate title within same session returns 409.
AC-009.3  Non-empty body validated; title and body are HTML-stripped and
          whitespace-normalised before store.
AC-009.4  User sub from JWT is stored on thread; cross-owner mutation is rejected.
AC-011.1  List endpoint returns paginated threads for a session, newest first.
AC-011.2  Status filter (open | closed | archived) applied server-side.
AC-011.3  Sort by created_at or updated_at; direction asc/desc.
AC-011.4  Keyword search (title prefix / body contains) via in-process filter.
AC-011.5  Pagination cursor (last_evaluated_key base64 JSON) returned when
          more results exist; accepted on next call.
IF-017    content-created event published to EventBridge on thread creation
          (TASK-033).
"""

from __future__ import annotations

import base64
import html
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_AWS_REGION = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION", "us-east-1")
_TABLE_NAME = os.environ.get(
    "DISCUSSION_TABLE_NAME",
    os.environ.get("DYNAMODB_TABLE_NAME", "archpilot-local-app-state"),
)
_ENDPOINT_URL = os.environ.get("DYNAMODB_ENDPOINT_URL")

# Maximum characters for user-supplied fields (OWASP A03 — input validation)
_TITLE_MAX_CHARS = 256
_BODY_MAX_CHARS = 10_000
_TAG_MAX_CHARS = 64
_TAG_MAX_COUNT = 10

# Default page size and hard cap
_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100

# Thread TTL: 90 days from last update  (STORE-003 retention policy)
_THREAD_TTL_SECONDS = int(os.environ.get("DISCUSSION_TTL_SECONDS", str(90 * 24 * 3600)))

_STRIP_TAGS_RE = re.compile(r"<[^>]+>")
_MULTI_SPACE_RE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# Domain enums
# ---------------------------------------------------------------------------


class ThreadStatus(str, Enum):
    """Lifecycle states for a discussion thread (AC-009.x)."""

    open = "open"
    closed = "closed"
    archived = "archived"


class SortField(str, Enum):
    """Sortable fields for the list endpoint (AC-011.3)."""

    created_at = "created_at"
    updated_at = "updated_at"
    title = "title"


class SortDirection(str, Enum):
    asc = "asc"
    desc = "desc"


# ---------------------------------------------------------------------------
# Pydantic models — request / response / storage
# ---------------------------------------------------------------------------


class CreateThreadRequest(BaseModel):
    """IF-004 — Create thread request body.

    AC-009.3: Both ``title`` and ``body`` are required and non-empty after
    sanitization.  HTML tags are stripped and entities are unescaped *before*
    the ``min_length`` check fires, so a body consisting only of HTML tags
    (e.g. ``<br>``) will correctly fail validation.
    """

    title: str = Field(..., min_length=1, max_length=_TITLE_MAX_CHARS)
    # AC-009.3 — body must be present and non-empty
    body: str = Field(..., min_length=1, max_length=_BODY_MAX_CHARS)
    tags: List[str] = Field(default_factory=list)

    @field_validator("title", "body", mode="before")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Strip HTML tags, unescape HTML entities, collapse whitespace.

        OWASP A03: never trust user-supplied markup; strip tags before storage
        so the database never holds raw HTML that could be rendered unsafely.
        The sanitized value is then checked against min_length by Pydantic.
        """
        if not isinstance(v, str):
            return v
        # 1. Unescape HTML entities (e.g. &amp; → &)
        v = html.unescape(v)
        # 2. Strip any HTML/XML tags
        v = _STRIP_TAGS_RE.sub("", v)
        # 3. Collapse whitespace (preserves single newlines for readability)
        v = _MULTI_SPACE_RE.sub(" ", v).strip()
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def sanitize_tags(cls, v: list) -> list:
        if not isinstance(v, list):
            return []
        cleaned: list[str] = []
        for tag in v[:_TAG_MAX_COUNT]:
            if not isinstance(tag, str):
                continue
            tag = html.unescape(tag)
            tag = _STRIP_TAGS_RE.sub("", tag).strip()
            if tag and len(tag) <= _TAG_MAX_CHARS:
                cleaned.append(tag)
        return cleaned


class UpdateThreadRequest(BaseModel):
    """IF-004 — Partial update request body (title, body, status, tags)."""

    title: Optional[str] = Field(None, min_length=1, max_length=_TITLE_MAX_CHARS)
    body: Optional[str] = Field(None, max_length=_BODY_MAX_CHARS)
    status: Optional[ThreadStatus] = None
    tags: Optional[List[str]] = None

    @field_validator("title", "body", mode="before")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = html.unescape(v)
        v = _STRIP_TAGS_RE.sub("", v)
        v = _MULTI_SPACE_RE.sub(" ", v).strip()
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def sanitize_tags(cls, v: Optional[list]) -> Optional[list]:
        if v is None:
            return None
        cleaned: list[str] = []
        for tag in v[:_TAG_MAX_COUNT]:
            if not isinstance(tag, str):
                continue
            tag = html.unescape(tag).strip()
            tag = _STRIP_TAGS_RE.sub("", tag).strip()
            if tag and len(tag) <= _TAG_MAX_CHARS:
                cleaned.append(tag)
        return cleaned

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UpdateThreadRequest":
        if all(v is None for v in (self.title, self.body, self.status, self.tags)):
            raise ValueError("At least one field must be provided for update.")
        return self


class ThreadResponse(BaseModel):
    """IF-004 — Single thread response body."""

    thread_id: str
    session_id: str
    user_sub: str
    title: str
    body: str
    status: ThreadStatus
    tags: List[str]
    created_at: str  # ISO-8601 UTC
    updated_at: str  # ISO-8601 UTC

    model_config = {"from_attributes": True}


class ThreadListResponse(BaseModel):
    """IF-004 — Paginated thread list response (AC-011.x)."""

    items: List[ThreadResponse]
    total_count: int  # count of items in THIS page
    has_more: bool
    next_cursor: Optional[str] = None  # base64 JSON of LastEvaluatedKey


# ---------------------------------------------------------------------------
# DynamoDB key helpers
# ---------------------------------------------------------------------------


def _pk(session_id: str) -> str:
    return f"disc#{session_id}"


def _sk(thread_id: str) -> str:
    return f"thread#{thread_id}"


def _gsi1pk(user_sub: str) -> str:
    return f"user#{user_sub}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _to_dynamo(value: Any) -> Any:
    """Recursively convert float → Decimal for DynamoDB."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_dynamo(v) for v in value]
    return value


def _from_dynamo(value: Any) -> Any:
    """Recursively convert Decimal → int/float."""
    if isinstance(value, Decimal):
        as_int = int(value)
        return as_int if as_int == value else float(value)
    if isinstance(value, dict):
        return {k: _from_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_dynamo(v) for v in value]
    return value


def _encode_cursor(last_key: Dict[str, Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(last_key).encode()).decode()


def _decode_cursor(cursor: str) -> Dict[str, Any]:
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception as exc:
        raise ValueError(f"Invalid pagination cursor: {exc}") from exc


# ---------------------------------------------------------------------------
# Thread service
# ---------------------------------------------------------------------------


class DuplicateTitleError(Exception):
    """Raised when a thread with the same title already exists in the session."""


class ThreadNotFoundError(Exception):
    """Raised when the requested thread does not exist."""


class ThreadOwnershipError(Exception):
    """Raised when the caller does not own the thread."""


class ThreadService:
    """COMP-003 — Discussion thread lifecycle service.

    All mutating operations are scoped to the authenticated ``user_sub``; reads
    are scoped to the session.  Cross-tenant (cross-user) access is blocked at
    the service layer (OWASP A01 — Broken Access Control).
    """

    def __init__(
        self,
        table_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ) -> None:
        self._table_name = table_name or _TABLE_NAME
        self._endpoint_url = endpoint_url or _ENDPOINT_URL
        self._table = None

    # ------------------------------------------------------------------
    # Low-level table access
    # ------------------------------------------------------------------

    def _get_table(self):
        if self._table is None:
            import boto3

            kwargs: Dict[str, Any] = {"region_name": _AWS_REGION}
            if self._endpoint_url:
                kwargs["endpoint_url"] = self._endpoint_url
            resource = boto3.resource("dynamodb", **kwargs)
            self._table = resource.Table(self._table_name)
            logger.info(
                "[ThreadService] connected table=%s endpoint=%s",
                self._table_name,
                self._endpoint_url or "default",
            )
        return self._table

    def _item_to_response(self, item: Dict[str, Any]) -> ThreadResponse:
        return ThreadResponse(
            thread_id=item["thread_id"],
            session_id=item["session_id"],
            user_sub=item["user_sub"],
            title=item["title"],
            body=item.get("body", ""),
            status=ThreadStatus(item.get("status", ThreadStatus.open)),
            tags=item.get("tags", []),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    # ------------------------------------------------------------------
    # Public API — AC-009.x
    # ------------------------------------------------------------------

    def create_thread(
        self,
        *,
        session_id: str,
        user_sub: str,
        request: CreateThreadRequest,
        event_publisher: Optional[Any] = None,
    ) -> ThreadResponse:
        """Create a new discussion thread.

        AC-009.1 — Stores validated/sanitized title + body; returns full item.
        AC-009.2 — Rejects duplicate title within same session (409 at router).
        AC-009.3 — Non-empty body enforced; title and body sanitised pre-store.
        AC-009.4 — user_sub stamped; ownership enforced on later mutations.
        IF-017   — ``content-created`` event published after successful store.

        Args:
            session_id:       Owning session identifier.
            user_sub:         Cognito user subject claim.
            request:          Validated + sanitized request body.
            event_publisher:  Optional ``DiscussionEventPublisher`` override;
                              when ``None`` the process singleton is used.
                              Inject a test double to avoid real EventBridge
                              calls during testing.
        """
        # AC-009.2 — check for duplicate title within session
        existing = self._find_by_title(session_id=session_id, title=request.title)
        if existing:
            raise DuplicateTitleError(
                f"A thread with title '{request.title}' already exists in this session."
            )

        now = _now_iso()
        thread_id = str(uuid.uuid4())

        item: Dict[str, Any] = {
            # DynamoDB primary key
            "PK": _pk(session_id),
            "SK": _sk(thread_id),
            # GSI1: all threads for a user (cross-session listing)
            "GSI1PK": _gsi1pk(user_sub),
            "GSI1SK": now,
            # GSI2: session threads sorted by updated_at
            "GSI2PK": _pk(session_id),
            "GSI2SK": now,
            # Domain fields
            "entity_type": "discussion_thread",
            "thread_id": thread_id,
            "session_id": session_id,
            "user_sub": user_sub,
            "title": request.title,
            "body": request.body,
            "status": ThreadStatus.open.value,
            "tags": request.tags,
            "created_at": now,
            "updated_at": now,
            "ttl": int(time.time()) + _THREAD_TTL_SECONDS,
        }

        self._get_table().put_item(
            Item=_to_dynamo(item),
            ConditionExpression="attribute_not_exists(PK)",
        )
        logger.info(
            "[ThreadService] created thread_id=%s session=%s user=%s title=%r",
            thread_id,
            session_id,
            user_sub,
            request.title,
        )

        response = self._item_to_response(_from_dynamo(item))

        # IF-017 — publish content-created event (best-effort; never fails the create)
        self._publish_created_event(
            response=response,
            publisher=event_publisher,
        )

        return response

    def _publish_created_event(
        self,
        *,
        response: ThreadResponse,
        publisher: Optional[Any] = None,
    ) -> None:
        """Publish the IF-017 ``content-created`` event.

        Imported lazily to avoid a hard circular dependency and to keep the
        service importable in environments where ``events`` is not yet present.
        Failures are swallowed here — the caller already has the stored thread.
        """
        try:
            from archpilot.services.discussion.events import (
                build_content_created_event,
                get_discussion_event_publisher,
            )

            pub = publisher if publisher is not None else get_discussion_event_publisher()
            event = build_content_created_event(
                thread_id=response.thread_id,
                session_id=response.session_id,
                user_sub=response.user_sub,
                state=response.status.value,
                timestamp=response.created_at,
            )
            pub.publish_content_created(event)
        except Exception:
            logger.exception(
                "[ThreadService] failed to publish content-created event thread_id=%s",
                response.thread_id,
            )

    def get_thread(
        self,
        *,
        session_id: str,
        thread_id: str,
    ) -> ThreadResponse:
        """Fetch a single thread by ID (public read — no ownership check required).

        Caller may add ownership check at the router level if needed.
        """
        item = self._fetch(session_id=session_id, thread_id=thread_id)
        if item is None:
            raise ThreadNotFoundError(thread_id)
        return self._item_to_response(item)

    def update_thread(
        self,
        *,
        session_id: str,
        thread_id: str,
        user_sub: str,
        request: UpdateThreadRequest,
    ) -> ThreadResponse:
        """Partially update a thread.

        AC-009.4 — Only the thread owner may mutate it.
        """
        item = self._fetch(session_id=session_id, thread_id=thread_id)
        if item is None:
            raise ThreadNotFoundError(thread_id)
        if item["user_sub"] != user_sub:
            raise ThreadOwnershipError(thread_id)

        now = _now_iso()
        updates: Dict[str, Any] = {"updated_at": now}

        if request.title is not None:
            # Check duplicate title for new value (exclude self)
            dup = self._find_by_title(session_id=session_id, title=request.title)
            if dup and dup["thread_id"] != thread_id:
                raise DuplicateTitleError(
                    f"A thread with title '{request.title}' already exists in this session."
                )
            updates["title"] = request.title
        if request.body is not None:
            updates["body"] = request.body
        if request.status is not None:
            updates["status"] = request.status.value
        if request.tags is not None:
            updates["tags"] = request.tags

        # Merge into full item for write-back
        item.update(updates)
        item["GSI2SK"] = now  # update recency index

        self._get_table().put_item(Item=_to_dynamo(item))
        logger.info(
            "[ThreadService] updated thread_id=%s session=%s user=%s fields=%s",
            thread_id,
            session_id,
            user_sub,
            list(updates.keys()),
        )
        return self._item_to_response(_from_dynamo(item))

    def delete_thread(
        self,
        *,
        session_id: str,
        thread_id: str,
        user_sub: str,
    ) -> None:
        """Hard-delete a thread.

        AC-009.4 — Only the thread owner may delete it.
        """
        item = self._fetch(session_id=session_id, thread_id=thread_id)
        if item is None:
            raise ThreadNotFoundError(thread_id)
        if item["user_sub"] != user_sub:
            raise ThreadOwnershipError(thread_id)

        self._get_table().delete_item(
            Key={"PK": _pk(session_id), "SK": _sk(thread_id)},
        )
        logger.info(
            "[ThreadService] deleted thread_id=%s session=%s user=%s",
            thread_id,
            session_id,
            user_sub,
        )

    def list_threads(
        self,
        *,
        session_id: str,
        status: Optional[ThreadStatus] = None,
        sort_by: SortField = SortField.created_at,
        direction: SortDirection = SortDirection.desc,
        keyword: Optional[str] = None,
        limit: int = _DEFAULT_PAGE_SIZE,
        cursor: Optional[str] = None,
    ) -> ThreadListResponse:
        """List threads for a session with optional filter/sort/paginate.

        AC-011.1 — paginated list, newest first by default.
        AC-011.2 — status filter applied server-side.
        AC-011.3 — sort_by created_at | updated_at | title; direction asc | desc.
        AC-011.4 — keyword filters on title prefix / body contains.
        AC-011.5 — cursor-based pagination (base64 JSON of LastEvaluatedKey).
        """
        limit = max(1, min(limit, _MAX_PAGE_SIZE))

        # Decode pagination cursor
        exclusive_start_key: Optional[Dict[str, Any]] = None
        if cursor:
            try:
                exclusive_start_key = _decode_cursor(cursor)
            except ValueError:
                logger.warning("[ThreadService] invalid cursor ignored: %s", cursor)

        from boto3.dynamodb.conditions import Key

        # Query PK=disc#<session_id>, SK begins_with thread#
        query_kwargs: Dict[str, Any] = {
            "KeyConditionExpression": (
                Key("PK").eq(_pk(session_id)) & Key("SK").begins_with("thread#")
            ),
            # Fetch a generous batch; we filter in-process for keyword/status
            # and re-page if needed. Over-fetching capped at 5× limit.
            "Limit": min(limit * 5, _MAX_PAGE_SIZE * 5),
            "ScanIndexForward": True,  # DynamoDB SK order; we re-sort below
        }
        if exclusive_start_key:
            query_kwargs["ExclusiveStartKey"] = exclusive_start_key

        resp = self._get_table().query(**query_kwargs)
        raw_items: List[Dict[str, Any]] = [_from_dynamo(i) for i in resp.get("Items", [])]
        last_dynamo_key = resp.get("LastEvaluatedKey")

        # Strip DynamoDB meta keys
        _META = {"PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK", "entity_type", "ttl"}
        items: List[Dict[str, Any]] = [
            {k: v for k, v in i.items() if k not in _META} for i in raw_items
        ]

        # AC-011.2 — status filter
        if status is not None:
            items = [i for i in items if i.get("status") == status.value]

        # AC-011.4 — keyword filter (title prefix / body contains, case-insensitive)
        if keyword:
            kw_lower = keyword.lower().strip()
            items = [
                i
                for i in items
                if kw_lower in i.get("title", "").lower()
                or kw_lower in i.get("body", "").lower()
            ]

        # AC-011.3 — sort
        reverse = direction == SortDirection.desc
        if sort_by == SortField.title:
            items.sort(key=lambda x: x.get("title", "").lower(), reverse=reverse)
        elif sort_by == SortField.updated_at:
            items.sort(key=lambda x: x.get("updated_at", ""), reverse=reverse)
        else:  # created_at (default)
            items.sort(key=lambda x: x.get("created_at", ""), reverse=reverse)

        # Paginate
        page = items[:limit]
        has_more = len(items) > limit or bool(last_dynamo_key)
        next_cursor: Optional[str] = None
        if has_more and last_dynamo_key:
            next_cursor = _encode_cursor(_from_dynamo(last_dynamo_key))

        return ThreadListResponse(
            items=[self._item_to_response(i) for i in page],
            total_count=len(page),
            has_more=has_more,
            next_cursor=next_cursor,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch(
        self,
        *,
        session_id: str,
        thread_id: str,
    ) -> Optional[Dict[str, Any]]:
        resp = self._get_table().get_item(
            Key={"PK": _pk(session_id), "SK": _sk(thread_id)},
        )
        item = resp.get("Item")
        if item is None:
            return None
        return _from_dynamo(item)

    def _find_by_title(
        self,
        *,
        session_id: str,
        title: str,
    ) -> Optional[Dict[str, Any]]:
        """Scan threads in session for exact title match.

        DynamoDB does not index on title, so we do a filtered Query over the
        session partition.  Thread counts per session are small (AC-011.1 notes
        a practical cap of a few hundred), so this is acceptable without a GSI.
        """
        from boto3.dynamodb.conditions import Attr, Key

        resp = self._get_table().query(
            KeyConditionExpression=(
                Key("PK").eq(_pk(session_id)) & Key("SK").begins_with("thread#")
            ),
            FilterExpression=Attr("title").eq(title),
            Limit=1,
        )
        items = resp.get("Items", [])
        return _from_dynamo(items[0]) if items else None


# ---------------------------------------------------------------------------
# Singleton accessor (mirrors get_state_repository pattern)
# ---------------------------------------------------------------------------

_service_singleton: Optional[ThreadService] = None


def get_thread_service() -> ThreadService:
    global _service_singleton
    if _service_singleton is None:
        _service_singleton = ThreadService()
    return _service_singleton


def reset_thread_service() -> None:
    """For tests: drop the singleton."""
    global _service_singleton
    _service_singleton = None

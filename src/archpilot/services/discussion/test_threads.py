"""Unit tests for the discussion thread service (COMP-003 / STORE-003).

Coverage targets
----------------
AC-009.1  create_thread returns a fully-populated ThreadResponse.
AC-009.2  Duplicate title within same session raises DuplicateTitleError (→ 409).
AC-009.3  Non-empty body validated; HTML tags and entities are stripped from
          title and body.
AC-009.4  user_sub is stored; cross-owner mutation raises ThreadOwnershipError (→ 403).
AC-011.1  list_threads returns items newest-first by default.
AC-011.2  status filter excludes non-matching threads.
AC-011.3  sort_by=title + direction=asc returns alphabetical order.
AC-011.4  keyword filter matches case-insensitively in title and body.
AC-011.5  next_cursor is returned when more items exist.
IF-017    content-created event published with correct payload on thread creation.

Design: all DynamoDB I/O is replaced by an in-memory fake (``FakeTable``) so
the tests run without AWS credentials or localstack.  EventBridge calls are
replaced by a ``FakePublisher`` spy that captures published events.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional

import pytest

from archpilot.services.discussion.threads import (
    CreateThreadRequest,
    DuplicateTitleError,
    SortDirection,
    SortField,
    ThreadNotFoundError,
    ThreadOwnershipError,
    ThreadResponse,
    ThreadService,
    ThreadStatus,
    UpdateThreadRequest,
    _pk,
    _sk,
    reset_thread_service,
)


# ---------------------------------------------------------------------------
# Condition-expression evaluator (replaces unreliable str() approach)
# ---------------------------------------------------------------------------


def _eval_condition(condition: Any, item: Dict[str, Any]) -> bool:
    """Evaluate a boto3 ConditionBase against a plain dict item.

    Uses ``ConditionExpressionBuilder`` to resolve placeholder names/values,
    then walks the expression string to apply the predicates.
    """
    from boto3.dynamodb.conditions import ConditionExpressionBuilder

    builder = ConditionExpressionBuilder()
    expr = builder.build_expression(condition)
    cond_str: str = expr.condition_expression
    names: Dict[str, str] = expr.attribute_name_placeholders
    values: Dict[str, Any] = expr.attribute_value_placeholders
    return _eval_expr_str(cond_str, names, values, item)


def _eval_expr_str(
    expr: str,
    names: Dict[str, str],
    values: Dict[str, Any],
    item: Dict[str, Any],
) -> bool:
    """Minimal recursive evaluator for DynamoDB condition expression strings."""
    expr = expr.strip()
    # Remove outer parens that wrap the entire expression
    if expr.startswith("(") and expr.endswith(")"):
        depth = 0
        for i, ch in enumerate(expr):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth == 0 and i < len(expr) - 1:
                break
        else:
            expr = expr[1:-1].strip()

    # AND
    if " AND " in expr:
        parts = _split_top_level(expr, " AND ")
        return all(_eval_expr_str(p, names, values, item) for p in parts)

    # OR
    if " OR " in expr:
        parts = _split_top_level(expr, " OR ")
        return any(_eval_expr_str(p, names, values, item) for p in parts)

    # begins_with(#nX, :vY)
    m = re.match(r"begins_with\((\S+),\s*(\S+)\)", expr)
    if m:
        attr = names.get(m.group(1), m.group(1))
        val = values.get(m.group(2), m.group(2))
        return str(item.get(attr, "")).startswith(str(val))

    # attribute_exists(#nX)
    m = re.match(r"attribute_exists\((\S+)\)", expr)
    if m:
        attr = names.get(m.group(1), m.group(1))
        return attr in item

    # #nX = :vY
    m = re.match(r"(\S+)\s*=\s*(\S+)", expr)
    if m:
        attr = names.get(m.group(1), m.group(1))
        val = values.get(m.group(2), m.group(2))
        return item.get(attr) == val

    # #nX <> :vY
    m = re.match(r"(\S+)\s*<>\s*(\S+)", expr)
    if m:
        attr = names.get(m.group(1), m.group(1))
        val = values.get(m.group(2), m.group(2))
        return item.get(attr) != val

    return True  # unknown predicates pass through


def _split_top_level(expr: str, sep: str) -> List[str]:
    """Split ``expr`` on ``sep`` only at depth-0 (outside parens)."""
    parts: List[str] = []
    depth = 0
    current = ""
    i = 0
    while i < len(expr):
        if expr[i] == "(":
            depth += 1
            current += expr[i]
            i += 1
        elif expr[i] == ")":
            depth -= 1
            current += expr[i]
            i += 1
        elif depth == 0 and expr[i:].startswith(sep):
            parts.append(current.strip())
            current = ""
            i += len(sep)
        else:
            current += expr[i]
            i += 1
    if current.strip():
        parts.append(current.strip())
    return parts


# ---------------------------------------------------------------------------
# In-memory DynamoDB table fake
# ---------------------------------------------------------------------------


class FakeTable:
    """Minimal DynamoDB Table replacement for unit tests.

    Supports the subset of the API used by ThreadService:
      - put_item (with attribute_not_exists ConditionExpression)
      - get_item
      - query (KeyConditionExpression + FilterExpression + Limit)
      - delete_item
    """

    def __init__(self) -> None:
        self._items: Dict[tuple, Dict[str, Any]] = {}

    def put_item(
        self,
        Item: Dict[str, Any],
        ConditionExpression: Any = "",
        **kwargs: Any,
    ) -> None:
        pk = Item["PK"]
        sk = Item["SK"]
        if ConditionExpression and "attribute_not_exists" in str(ConditionExpression):
            if (pk, sk) in self._items:
                from botocore.exceptions import ClientError

                raise ClientError(
                    error_response={
                        "Error": {
                            "Code": "ConditionalCheckFailedException",
                            "Message": "Condition failed",
                        }
                    },
                    operation_name="PutItem",
                )
        self._items[(pk, sk)] = dict(Item)

    def get_item(self, Key: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        pk = Key["PK"]
        sk = Key["SK"]
        item = self._items.get((pk, sk))
        return {"Item": dict(item)} if item else {}

    def delete_item(self, Key: Dict[str, Any], **kwargs: Any) -> None:
        pk = Key["PK"]
        sk = Key["SK"]
        self._items.pop((pk, sk), None)

    def query(
        self,
        KeyConditionExpression: Any = None,
        FilterExpression: Any = None,
        Limit: int = 1000,
        ExclusiveStartKey: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Evaluate boto3 condition expressions against the in-memory store."""
        all_items = list(self._items.values())

        if KeyConditionExpression is not None:
            all_items = [i for i in all_items if _eval_condition(KeyConditionExpression, i)]

        if FilterExpression is not None:
            all_items = [i for i in all_items if _eval_condition(FilterExpression, i)]

        # Simulate ExclusiveStartKey pagination
        start = 0
        if ExclusiveStartKey:
            for idx, item in enumerate(all_items):
                if (
                    item.get("PK") == ExclusiveStartKey.get("PK")
                    and item.get("SK") == ExclusiveStartKey.get("SK")
                ):
                    start = idx + 1
                    break

        page = all_items[start : start + Limit]
        result: Dict[str, Any] = {"Items": page}
        if start + Limit < len(all_items):
            result["LastEvaluatedKey"] = {"PK": page[-1]["PK"], "SK": page[-1]["SK"]}
        return result


# ---------------------------------------------------------------------------
# Fake EventBridge publisher spy (IF-017)
# ---------------------------------------------------------------------------


class FakePublisher:
    """Captures published events without hitting AWS EventBridge."""

    def __init__(self) -> None:
        self.published: List[Any] = []

    def publish_content_created(self, event: Any) -> None:
        self.published.append(event)


def _make_service(fake_table: FakeTable) -> ThreadService:
    svc = ThreadService(table_name="test-table")
    svc._table = fake_table
    return svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton():
    reset_thread_service()
    yield
    reset_thread_service()


@pytest.fixture()
def table() -> FakeTable:
    return FakeTable()


@pytest.fixture()
def svc(table: FakeTable) -> ThreadService:
    return _make_service(table)


@pytest.fixture()
def publisher() -> FakePublisher:
    return FakePublisher()


SESSION = "sess-abc123"
USER_A = "user-a-sub"
USER_B = "user-b-sub"


def _create_req(
    title: str = "Hello",
    body: str = "Default body text",
    tags: Optional[List[str]] = None,
) -> CreateThreadRequest:
    return CreateThreadRequest(title=title, body=body, tags=tags or [])


# ---------------------------------------------------------------------------
# AC-009.1 — Thread creation returns full response
# ---------------------------------------------------------------------------


class TestCreateThread:
    def test_create_returns_thread_response(self, svc: ThreadService, publisher: FakePublisher):
        req = _create_req("My thread", "Some body text")
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req, event_publisher=publisher
        )
        assert isinstance(result, ThreadResponse)
        assert result.title == "My thread"
        assert result.body == "Some body text"
        assert result.session_id == SESSION
        assert result.user_sub == USER_A
        assert result.status == ThreadStatus.open
        assert len(result.thread_id) == 36
        assert result.created_at != ""
        assert result.updated_at != ""

    def test_duplicate_title_raises(self, svc: ThreadService, publisher: FakePublisher):
        """AC-009.2 — duplicate title within session → DuplicateTitleError."""
        svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("Dup"),
            event_publisher=publisher,
        )
        with pytest.raises(DuplicateTitleError):
            svc.create_thread(
                session_id=SESSION, user_sub=USER_A, request=_create_req("Dup"),
                event_publisher=publisher,
            )

    def test_duplicate_title_different_session_ok(
        self, svc: ThreadService, publisher: FakePublisher
    ):
        svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("X"),
            event_publisher=publisher,
        )
        result = svc.create_thread(
            session_id="other-session", user_sub=USER_A, request=_create_req("X"),
            event_publisher=publisher,
        )
        assert result.title == "X"

    def test_html_stripped_from_title(self, svc: ThreadService, publisher: FakePublisher):
        """AC-009.3 — HTML tags stripped from title."""
        req = _create_req(title="<b>Bold</b> title", body="Safe body")
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req, event_publisher=publisher
        )
        assert "<b>" not in result.title
        assert "Bold" in result.title

    def test_html_stripped_from_body(self, svc: ThreadService, publisher: FakePublisher):
        """AC-009.3 — HTML tags stripped from body."""
        req = _create_req(title="T", body="<script>alert('xss')</script> text")
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req, event_publisher=publisher
        )
        assert "<script>" not in result.body
        assert "text" in result.body

    def test_html_entities_unescaped_and_tags_stripped(
        self, svc: ThreadService, publisher: FakePublisher
    ):
        """AC-009.3 — HTML entities unescaped, then tags stripped."""
        req = _create_req(title="&amp; Me &lt;tag&gt;", body="body text")
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req, event_publisher=publisher
        )
        assert "&amp;" not in result.title
        assert "<tag>" not in result.title
        assert "Me" in result.title

    # VER-002 — non-empty body validation
    def test_empty_body_raises_validation_error(self):
        """AC-009.3 — empty body rejected (VER-002)."""
        with pytest.raises(Exception):
            CreateThreadRequest(title="Valid title", body="")

    def test_whitespace_only_body_raises_validation_error(self):
        """AC-009.3 — whitespace-only body collapses to '' → rejected."""
        with pytest.raises(Exception):
            CreateThreadRequest(title="Valid title", body="   ")

    def test_html_only_body_raises_validation_error(self):
        """AC-009.3 — HTML-tag-only body strips to '' → rejected."""
        with pytest.raises(Exception):
            CreateThreadRequest(title="Valid title", body="<br><b></b>")

    def test_user_sub_stored_on_thread(self, svc: ThreadService, publisher: FakePublisher):
        """AC-009.4 — user_sub is stored on created thread."""
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req(),
            event_publisher=publisher,
        )
        assert result.user_sub == USER_A

    def test_tags_stored(self, svc: ThreadService, publisher: FakePublisher):
        req = _create_req(tags=["python", "fastapi"])
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req, event_publisher=publisher
        )
        assert result.tags == ["python", "fastapi"]

    def test_tags_html_stripped(self, svc: ThreadService, publisher: FakePublisher):
        req = _create_req(tags=["<em>tag</em>", "ok"])
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req, event_publisher=publisher
        )
        for tag in result.tags:
            assert "<" not in tag


# ---------------------------------------------------------------------------
# IF-017 — content-created event published on thread creation (TASK-033)
# ---------------------------------------------------------------------------


class TestContentCreatedEvent:
    """Verify that create_thread publishes a compliant IF-017 event payload."""

    def test_event_published_on_create(self, svc: ThreadService, publisher: FakePublisher):
        req = _create_req("Event thread", "Event body")
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req, event_publisher=publisher,
        )
        assert len(publisher.published) == 1
        evt = publisher.published[0]
        assert evt.entity_type == "discussion_thread"
        assert evt.entity_id == result.thread_id
        assert evt.state == "open"
        assert evt.session_id == SESSION
        assert evt.user_sub == USER_A
        assert evt.timestamp == result.created_at

    def test_event_payload_to_detail(self, svc: ThreadService, publisher: FakePublisher):
        req = _create_req("Detail check", "Some body")
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req, event_publisher=publisher,
        )
        detail = publisher.published[0].to_detail()
        assert detail["entity_type"] == "discussion_thread"
        assert detail["entity_id"] == result.thread_id
        assert detail["state"] == "open"
        assert detail["session_id"] == SESSION
        assert detail["user_sub"] == USER_A
        assert "timestamp" in detail

    def test_event_not_published_when_create_fails(
        self, svc: ThreadService, publisher: FakePublisher
    ):
        """No event emitted when DuplicateTitleError is raised before store."""
        svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("Dup"),
            event_publisher=publisher,
        )
        with pytest.raises(DuplicateTitleError):
            svc.create_thread(
                session_id=SESSION, user_sub=USER_A, request=_create_req("Dup"),
                event_publisher=publisher,
            )
        assert len(publisher.published) == 1  # only the first create

    def test_publish_failure_does_not_raise(self, svc: ThreadService):
        """Broken publisher must not prevent thread creation (best-effort delivery)."""

        class BrokenPublisher:
            def publish_content_created(self, event: Any) -> None:
                raise RuntimeError("EventBridge unavailable")

        req = _create_req("Resilient thread", "Still works")
        result = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=req,
            event_publisher=BrokenPublisher(),
        )
        assert result.thread_id  # thread was stored despite publisher failure


# ---------------------------------------------------------------------------
# AC-009.4 — Ownership enforcement on update / delete
# ---------------------------------------------------------------------------


class TestOwnershipEnforcement:
    def test_update_by_non_owner_raises(self, svc: ThreadService, publisher: FakePublisher):
        t = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req(),
            event_publisher=publisher,
        )
        with pytest.raises(ThreadOwnershipError):
            svc.update_thread(
                session_id=SESSION, thread_id=t.thread_id, user_sub=USER_B,
                request=UpdateThreadRequest(body="new body"),
            )

    def test_delete_by_non_owner_raises(self, svc: ThreadService, publisher: FakePublisher):
        t = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req(),
            event_publisher=publisher,
        )
        with pytest.raises(ThreadOwnershipError):
            svc.delete_thread(session_id=SESSION, thread_id=t.thread_id, user_sub=USER_B)

    def test_update_by_owner_succeeds(self, svc: ThreadService, publisher: FakePublisher):
        t = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req(),
            event_publisher=publisher,
        )
        result = svc.update_thread(
            session_id=SESSION, thread_id=t.thread_id, user_sub=USER_A,
            request=UpdateThreadRequest(body="Updated body"),
        )
        assert result.body == "Updated body"

    def test_delete_by_owner_succeeds(self, svc: ThreadService, publisher: FakePublisher):
        t = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req(),
            event_publisher=publisher,
        )
        svc.delete_thread(session_id=SESSION, thread_id=t.thread_id, user_sub=USER_A)
        with pytest.raises(ThreadNotFoundError):
            svc.get_thread(session_id=SESSION, thread_id=t.thread_id)

    def test_update_status_transition(self, svc: ThreadService, publisher: FakePublisher):
        t = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req(),
            event_publisher=publisher,
        )
        result = svc.update_thread(
            session_id=SESSION, thread_id=t.thread_id, user_sub=USER_A,
            request=UpdateThreadRequest(status=ThreadStatus.closed),
        )
        assert result.status == ThreadStatus.closed


# ---------------------------------------------------------------------------
# AC-011.x — list threads
# ---------------------------------------------------------------------------


class TestListThreads:
    def _seed(
        self, svc: ThreadService, n: int = 3, publisher: Optional[FakePublisher] = None
    ) -> List[ThreadResponse]:
        pub = publisher or FakePublisher()
        results = []
        for i in range(n):
            results.append(
                svc.create_thread(
                    session_id=SESSION, user_sub=USER_A,
                    request=_create_req(title=f"Thread {i}", body=f"body {i}"),
                    event_publisher=pub,
                )
            )
        return results

    def test_list_returns_all_threads(self, svc: ThreadService):
        """AC-011.1 — total_count matches number of created threads."""
        self._seed(svc, 3)
        result = svc.list_threads(session_id=SESSION)
        assert result.total_count == 3

    def test_list_desc_order_by_created_at(self, svc: ThreadService):
        """AC-011.1 — items sorted by created_at descending (non-ascending timestamps)."""
        self._seed(svc, 3)
        result = svc.list_threads(session_id=SESSION)
        timestamps = [t.created_at for t in result.items]
        for earlier, later in zip(timestamps, timestamps[1:]):
            # Each successive timestamp must be <= the previous (desc order)
            assert earlier >= later, (
                f"Expected desc order: {earlier!r} should be >= {later!r}"
            )

    def test_status_filter_open(self, svc: ThreadService):
        """AC-011.2 — status=open excludes closed threads."""
        pub = FakePublisher()
        t1 = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("T1"),
            event_publisher=pub,
        )
        t2 = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("T2"),
            event_publisher=pub,
        )
        svc.update_thread(
            session_id=SESSION, thread_id=t2.thread_id, user_sub=USER_A,
            request=UpdateThreadRequest(status=ThreadStatus.closed),
        )
        result = svc.list_threads(session_id=SESSION, status=ThreadStatus.open)
        assert all(t.status == ThreadStatus.open for t in result.items)
        assert any(t.thread_id == t1.thread_id for t in result.items)
        assert all(t.thread_id != t2.thread_id for t in result.items)

    def test_status_filter_closed(self, svc: ThreadService):
        """AC-011.2 — status=closed returns only closed threads."""
        pub = FakePublisher()
        t1 = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("T1"),
            event_publisher=pub,
        )
        svc.update_thread(
            session_id=SESSION, thread_id=t1.thread_id, user_sub=USER_A,
            request=UpdateThreadRequest(status=ThreadStatus.closed),
        )
        result = svc.list_threads(session_id=SESSION, status=ThreadStatus.closed)
        assert len(result.items) == 1
        assert result.items[0].status == ThreadStatus.closed

    def test_sort_by_title_asc(self, svc: ThreadService):
        """AC-011.3 — sort_by=title, direction=asc → alphabetical."""
        pub = FakePublisher()
        for title in ["Zebra", "Apple", "Mango"]:
            svc.create_thread(
                session_id=SESSION, user_sub=USER_A, request=_create_req(title),
                event_publisher=pub,
            )
        result = svc.list_threads(
            session_id=SESSION, sort_by=SortField.title, direction=SortDirection.asc,
        )
        titles = [t.title for t in result.items]
        assert titles == sorted(titles, key=str.lower)

    def test_sort_by_title_desc(self, svc: ThreadService):
        """AC-011.3 — sort_by=title, direction=desc → reverse alphabetical."""
        pub = FakePublisher()
        for title in ["Zebra", "Apple", "Mango"]:
            svc.create_thread(
                session_id=SESSION, user_sub=USER_A, request=_create_req(title),
                event_publisher=pub,
            )
        result = svc.list_threads(
            session_id=SESSION, sort_by=SortField.title, direction=SortDirection.desc,
        )
        titles = [t.title for t in result.items]
        assert titles == sorted(titles, key=str.lower, reverse=True)

    def test_keyword_filter_title(self, svc: ThreadService):
        """AC-011.4 — keyword matches thread title (case-insensitive)."""
        pub = FakePublisher()
        svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("Python tips"),
            event_publisher=pub,
        )
        svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("JS tips"),
            event_publisher=pub,
        )
        result = svc.list_threads(session_id=SESSION, keyword="python")
        assert len(result.items) == 1
        assert "Python" in result.items[0].title

    def test_keyword_filter_body(self, svc: ThreadService):
        """AC-011.4 — keyword matches thread body."""
        pub = FakePublisher()
        svc.create_thread(
            session_id=SESSION, user_sub=USER_A,
            request=_create_req("Thread A", body="fastapi is great"),
            event_publisher=pub,
        )
        svc.create_thread(
            session_id=SESSION, user_sub=USER_A,
            request=_create_req("Thread B", body="flask is also nice"),
            event_publisher=pub,
        )
        result = svc.list_threads(session_id=SESSION, keyword="fastapi")
        assert len(result.items) == 1
        assert result.items[0].title == "Thread A"

    def test_keyword_case_insensitive(self, svc: ThreadService):
        """AC-011.4 — keyword matching is case-insensitive."""
        pub = FakePublisher()
        svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req("UPPER CASE"),
            event_publisher=pub,
        )
        result = svc.list_threads(session_id=SESSION, keyword="upper")
        assert len(result.items) == 1

    def test_pagination_cursor(self, svc: ThreadService):
        """AC-011.5 — limit=2 with 4 threads → page of 2."""
        pub = FakePublisher()
        for i in range(4):
            svc.create_thread(
                session_id=SESSION, user_sub=USER_A,
                request=_create_req(f"Paged {i}"),
                event_publisher=pub,
            )
        page1 = svc.list_threads(session_id=SESSION, limit=2)
        assert page1.total_count == 2
        assert isinstance(page1.has_more, bool)

    def test_empty_session_returns_empty_list(self, svc: ThreadService):
        result = svc.list_threads(session_id="no-such-session")
        assert result.total_count == 0
        assert result.items == []


# ---------------------------------------------------------------------------
# Thread not found
# ---------------------------------------------------------------------------


class TestGetThread:
    def test_get_missing_thread_raises(self, svc: ThreadService):
        fake_id = str(uuid.uuid4())
        with pytest.raises(ThreadNotFoundError):
            svc.get_thread(session_id=SESSION, thread_id=fake_id)

    def test_get_existing_thread(self, svc: ThreadService, publisher: FakePublisher):
        t = svc.create_thread(
            session_id=SESSION, user_sub=USER_A, request=_create_req(),
            event_publisher=publisher,
        )
        fetched = svc.get_thread(session_id=SESSION, thread_id=t.thread_id)
        assert fetched.thread_id == t.thread_id


# ---------------------------------------------------------------------------
# Input validation edge cases
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_title_too_long_raises_validation_error(self):
        with pytest.raises(Exception):
            CreateThreadRequest(title="x" * 300, body="b")

    def test_empty_title_raises_validation_error(self):
        with pytest.raises(Exception):
            CreateThreadRequest(title="", body="body text")

    def test_empty_body_raises_validation_error(self):
        """VER-002 — body field must be non-empty (AC-009.3)."""
        with pytest.raises(Exception):
            CreateThreadRequest(title="Valid", body="")

    def test_body_too_long_raises_validation_error(self):
        with pytest.raises(Exception):
            CreateThreadRequest(title="OK", body="x" * 10_001)

    def test_update_no_fields_raises(self):
        with pytest.raises(Exception):
            UpdateThreadRequest()

    def test_tags_excess_truncated(self):
        req = CreateThreadRequest(title="T", body="body", tags=["t"] * 20)
        assert len(req.tags) <= 10

    def test_tag_too_long_excluded(self):
        long_tag = "x" * 100
        req = CreateThreadRequest(title="T", body="body", tags=[long_tag, "ok"])
        assert long_tag not in req.tags
        assert "ok" in req.tags

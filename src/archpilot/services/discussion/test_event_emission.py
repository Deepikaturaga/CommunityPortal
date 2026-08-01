"""Integration tests — event emission via the HTTP layer (IF-017 / TASK-033).

These tests exercise the full FastAPI request/response cycle for the
discussion thread router, asserting that a ``content-created`` EventBridge
event is emitted exactly once per successful ``POST`` and is NOT emitted when
the request fails (duplicate title → 409).

Design decisions
----------------
- A **minimal FastAPI app** is assembled here so tests are fully isolated from
  unrelated routers that are not present in this repository snapshot.
- ``FakeTable`` (in-memory DynamoDB) and ``FakePublisher`` (event spy) are
  injected via FastAPI ``dependency_overrides`` — no AWS credentials required.
- ``get_current_user`` is overridden to return a fixed ``CognitoUser`` with a
  known ``user_sub``, avoiding any JWT logic.
- All tests are synchronous (``TestClient`` wraps the ASGI app with
  ``requests`` under the hood); ``pytest-asyncio`` is NOT needed here.
- ``AUTH_STUB_ENABLED`` env var is NOT required because the dependency is
  overridden entirely.

Acceptance criteria validated
------------------------------
IF-017   content-created event published on successful thread creation.
         - event.entity_type == "discussion_thread"
         - event.entity_id   == thread_id returned in response
         - event.state       == "open"
         - event.session_id  == session_id path param
         - event.user_sub    == authenticated user sub
         - event.timestamp   == created_at in response
         - event.to_detail() is a JSON-serialisable dict with all six keys

AC-009.2 / IF-017  No event emitted when duplicate title → 409.
IF-017            Publisher failure does NOT cause 5xx (best-effort delivery).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from archpilot.api.cognito_auth import CognitoUser, get_current_user
from archpilot.api.routers.discussion_router import discussion_router
from archpilot.services.discussion.events import (
    ContentCreatedEvent,
    DiscussionEventPublisher,
    get_discussion_event_publisher,
    reset_discussion_event_publisher,
)
from archpilot.services.discussion.threads import (
    ThreadService,
    get_thread_service,
    reset_thread_service,
)


# ---------------------------------------------------------------------------
# Re-use the in-memory fakes from the unit-test module
# (avoids duplication; the fakes live in test_threads.py which is co-located
# with the service under ``src/``, making them importable as a test utility)
# ---------------------------------------------------------------------------

from archpilot.services.discussion.test_threads import FakePublisher, FakeTable


# ---------------------------------------------------------------------------
# Shared test constants
# ---------------------------------------------------------------------------

_SESSION_ID = "test-sess-001"
_USER_SUB = "cognito-user-abc"
_AUTH_HEADERS = {"X-User-Sub": _USER_SUB}  # only used if stub dep is active


# ---------------------------------------------------------------------------
# App + client fixtures
# ---------------------------------------------------------------------------


def _build_app(
    fake_table: FakeTable,
    fake_publisher: FakePublisher,
) -> FastAPI:
    """Construct a minimal FastAPI app with the discussion router and DI overrides."""
    app = FastAPI(title="archpilot-test")
    app.include_router(discussion_router, prefix="/api")

    # Override ThreadService to inject our FakeTable
    def _fake_thread_service() -> ThreadService:
        svc = ThreadService(table_name="test-table")
        svc._table = fake_table
        # Monkey-patch _publish_created_event so it uses our FakePublisher
        # instead of the process singleton.  This mirrors the contract that
        # ThreadService.create_thread(..., event_publisher=X) uses when an
        # explicit publisher is provided; here we force it via the service
        # layer so the router's default call path (no explicit publisher arg)
        # is exercised end-to-end.
        original_publish = svc._publish_created_event

        def _patched_publish(*, response, publisher=None):
            original_publish(response=response, publisher=fake_publisher)

        svc._publish_created_event = _patched_publish
        return svc

    # Override auth dependency to return a fixed user
    def _fake_current_user() -> CognitoUser:
        return CognitoUser(sub=_USER_SUB, email="test@example.com")

    app.dependency_overrides[get_thread_service] = _fake_thread_service
    app.dependency_overrides[get_current_user] = _fake_current_user

    return app


@pytest.fixture(autouse=True)
def _reset_singletons():
    reset_thread_service()
    reset_discussion_event_publisher()
    yield
    reset_thread_service()
    reset_discussion_event_publisher()


@pytest.fixture()
def table() -> FakeTable:
    return FakeTable()


@pytest.fixture()
def publisher() -> FakePublisher:
    return FakePublisher()


@pytest.fixture()
def client(table: FakeTable, publisher: FakePublisher) -> TestClient:
    app = _build_app(table, publisher)
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _post_thread(
    client: TestClient,
    *,
    session_id: str = _SESSION_ID,
    title: str = "Integration thread",
    body: str = "Integration body text",
    tags: Optional[List[str]] = None,
) -> Any:
    payload: Dict[str, Any] = {"title": title, "body": body}
    if tags is not None:
        payload["tags"] = tags
    return client.post(
        f"/api/discussion/sessions/{session_id}/threads",
        json=payload,
    )


# ---------------------------------------------------------------------------
# IF-017 — event emitted on successful thread creation
# ---------------------------------------------------------------------------


class TestEventEmissionOnCreate:
    """Integration tests: HTTP POST → ThreadService → DiscussionEventPublisher (IF-017)."""

    def test_single_event_emitted_on_201(self, client: TestClient, publisher: FakePublisher):
        """Exactly one event is captured when a thread is created successfully."""
        resp = _post_thread(client, title="My first thread", body="Some great content")

        assert resp.status_code == 201, resp.text
        assert len(publisher.published) == 1

    def test_event_entity_type(self, client: TestClient, publisher: FakePublisher):
        """IF-017: entity_type must be ``discussion_thread``."""
        _post_thread(client)
        evt: ContentCreatedEvent = publisher.published[0]
        assert evt.entity_type == "discussion_thread"

    def test_event_entity_id_matches_response(self, client: TestClient, publisher: FakePublisher):
        """IF-017: entity_id matches the thread_id returned in the HTTP response."""
        resp = _post_thread(client, title="ID check", body="Body text")
        assert resp.status_code == 201
        thread_id = resp.json()["thread_id"]

        evt: ContentCreatedEvent = publisher.published[0]
        assert evt.entity_id == thread_id

    def test_event_state_is_open(self, client: TestClient, publisher: FakePublisher):
        """IF-017: newly created thread state must be ``open``."""
        _post_thread(client)
        evt: ContentCreatedEvent = publisher.published[0]
        assert evt.state == "open"

    def test_event_session_id(self, client: TestClient, publisher: FakePublisher):
        """IF-017: session_id in event matches the path parameter."""
        session = "special-session-99"
        _post_thread(client, session_id=session)
        evt: ContentCreatedEvent = publisher.published[0]
        assert evt.session_id == session

    def test_event_user_sub(self, client: TestClient, publisher: FakePublisher):
        """IF-017: user_sub in event matches the authenticated caller."""
        _post_thread(client)
        evt: ContentCreatedEvent = publisher.published[0]
        assert evt.user_sub == _USER_SUB

    def test_event_timestamp_matches_response(self, client: TestClient, publisher: FakePublisher):
        """IF-017: timestamp in event matches created_at in the HTTP response body."""
        resp = _post_thread(client, title="Timestamp check", body="Body text")
        assert resp.status_code == 201
        created_at = resp.json()["created_at"]

        evt: ContentCreatedEvent = publisher.published[0]
        assert evt.timestamp == created_at

    def test_event_to_detail_is_json_serialisable(
        self, client: TestClient, publisher: FakePublisher
    ):
        """IF-017: to_detail() produces a JSON-serialisable dict with the six required keys."""
        _post_thread(client)
        detail = publisher.published[0].to_detail()

        # Must contain all six IF-017 keys
        for key in ("entity_type", "entity_id", "state", "session_id", "user_sub", "timestamp"):
            assert key in detail, f"Missing key: {key}"

        # Must be fully JSON-serialisable (no Decimal, datetime, etc.)
        serialised = json.dumps(detail)
        roundtrip = json.loads(serialised)
        assert roundtrip["entity_type"] == "discussion_thread"

    def test_full_detail_payload_values(self, client: TestClient, publisher: FakePublisher):
        """IF-017: full detail dict correctness in one shot."""
        resp = _post_thread(client, title="Full payload", body="Detailed body")
        assert resp.status_code == 201
        body = resp.json()

        detail = publisher.published[0].to_detail()
        assert detail["entity_type"] == "discussion_thread"
        assert detail["entity_id"] == body["thread_id"]
        assert detail["state"] == "open"
        assert detail["session_id"] == _SESSION_ID
        assert detail["user_sub"] == _USER_SUB
        assert detail["timestamp"] == body["created_at"]

    def test_multiple_creates_emit_multiple_events(
        self, client: TestClient, publisher: FakePublisher
    ):
        """Each successful create produces exactly one event; three creates → three events."""
        for i in range(3):
            resp = _post_thread(client, title=f"Thread {i}", body="Body")
            assert resp.status_code == 201

        assert len(publisher.published) == 3
        # Each event must have a unique entity_id
        ids = {e.entity_id for e in publisher.published}
        assert len(ids) == 3


# ---------------------------------------------------------------------------
# AC-009.2 / IF-017 — no event on failure paths
# ---------------------------------------------------------------------------


class TestEventNotEmittedOnFailure:
    """Events must NOT be emitted when the thread creation request fails."""

    def test_no_event_on_duplicate_title_409(
        self, client: TestClient, publisher: FakePublisher
    ):
        """AC-009.2 + IF-017: duplicate title → 409; no second event emitted."""
        # First create succeeds and emits one event
        resp1 = _post_thread(client, title="Duplicate title", body="First body")
        assert resp1.status_code == 201
        assert len(publisher.published) == 1

        # Second create with same title → 409; no additional event
        resp2 = _post_thread(client, title="Duplicate title", body="Second body")
        assert resp2.status_code == 409
        assert len(publisher.published) == 1, (
            "No additional event should be emitted on duplicate-title error"
        )

    def test_no_event_on_validation_error_422(
        self, client: TestClient, publisher: FakePublisher
    ):
        """Invalid request body → 422; zero events emitted."""
        resp = client.post(
            f"/api/discussion/sessions/{_SESSION_ID}/threads",
            json={"title": "", "body": ""},  # both empty — fails Pydantic validation
        )
        assert resp.status_code == 422
        assert len(publisher.published) == 0

    def test_no_event_on_missing_body_field(
        self, client: TestClient, publisher: FakePublisher
    ):
        """Missing required ``body`` field → 422; zero events emitted."""
        resp = client.post(
            f"/api/discussion/sessions/{_SESSION_ID}/threads",
            json={"title": "No body field"},
        )
        assert resp.status_code == 422
        assert len(publisher.published) == 0

    def test_no_event_on_html_only_body_422(
        self, client: TestClient, publisher: FakePublisher
    ):
        """HTML-tag-only body strips to empty → 422; zero events emitted."""
        resp = _post_thread(client, title="HTML-only body", body="<br><b></b>")
        assert resp.status_code == 422
        assert len(publisher.published) == 0


# ---------------------------------------------------------------------------
# IF-017 (resilience) — publisher failure must not cause 5xx
# ---------------------------------------------------------------------------


class TestEventPublisherResilience:
    """A broken publisher must not prevent thread creation (best-effort delivery)."""

    def test_broken_publisher_does_not_cause_500(self, table: FakeTable):
        """RuntimeError in publisher is swallowed; thread still returns 201."""

        class BrokenPublisher:
            def publish_content_created(self, event: Any) -> None:
                raise RuntimeError("EventBridge unavailable")

        broken_pub = BrokenPublisher()

        app = FastAPI(title="archpilot-broken-pub-test")
        app.include_router(discussion_router, prefix="/api")

        def _svc() -> ThreadService:
            svc = ThreadService(table_name="test-table")
            svc._table = table
            original = svc._publish_created_event

            def _patched(*, response, publisher=None):
                original(response=response, publisher=broken_pub)

            svc._publish_created_event = _patched
            return svc

        def _user() -> CognitoUser:
            return CognitoUser(sub=_USER_SUB)

        app.dependency_overrides[get_thread_service] = _svc
        app.dependency_overrides[get_current_user] = _user

        with TestClient(app, raise_server_exceptions=True) as tc:
            resp = tc.post(
                f"/api/discussion/sessions/{_SESSION_ID}/threads",
                json={"title": "Resilient thread", "body": "Still works"},
            )
        assert resp.status_code == 201
        assert resp.json()["thread_id"]

    def test_broken_publisher_thread_persisted(self, table: FakeTable):
        """Thread is stored in the FakeTable even when the publisher raises."""

        class BrokenPublisher:
            def publish_content_created(self, event: Any) -> None:
                raise RuntimeError("EventBridge unavailable")

        broken_pub = BrokenPublisher()

        app = FastAPI(title="archpilot-persist-test")
        app.include_router(discussion_router, prefix="/api")
        stored_ids: List[str] = []

        def _svc() -> ThreadService:
            svc = ThreadService(table_name="test-table")
            svc._table = table

            original_create = svc.create_thread

            def _patched_create(**kwargs):
                result = original_create(**kwargs, event_publisher=broken_pub)
                stored_ids.append(result.thread_id)
                return result

            svc.create_thread = _patched_create
            return svc

        def _user() -> CognitoUser:
            return CognitoUser(sub=_USER_SUB)

        app.dependency_overrides[get_thread_service] = _svc
        app.dependency_overrides[get_current_user] = _user

        with TestClient(app, raise_server_exceptions=True) as tc:
            resp = tc.post(
                f"/api/discussion/sessions/{_SESSION_ID}/threads",
                json={"title": "Persist check", "body": "Body text"},
            )

        assert resp.status_code == 201
        assert len(stored_ids) == 1

        # Verify the item is actually in the FakeTable
        from archpilot.services.discussion.threads import _pk, _sk

        key = (_pk(_SESSION_ID), _sk(stored_ids[0]))
        assert key in table._items, "Thread item must be present in FakeTable after broken publisher"

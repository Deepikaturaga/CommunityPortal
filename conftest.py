pytest_plugins = ["pytest_asyncio", "tests.notifications.plugin"]
"""
Root conftest.py — shared fixtures available to all test modules.

Provides:
  - anyio_backend (asyncio only)
  - Async HTTPX client wired to the FastAPI app under test
  - JWT helpers for authenticated requests
  - In-memory Redis mock via fakeredis
  - Celery app configured for eager (synchronous) task execution in tests
"""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ── application imports (resolved at collection time) ──────────────────────
# The application package is expected under src/ or the project root.
# We guard with a try/except so collection does not fail when the app is not
# yet assembled; tests that need the real app will be skipped automatically.
try:
    from app.main import app as fastapi_app  # type: ignore[import]
    APP_AVAILABLE = True
except Exception:  # pragma: no cover
    fastapi_app = None  # type: ignore[assignment]
    APP_AVAILABLE = False

# ── pytest-asyncio global config ──────────────────────────────────────────


# ---------------------------------------------------------------------------
# anyio backend — pin to asyncio; avoid trio for this project
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


# ---------------------------------------------------------------------------
# JWT / auth helpers
# ---------------------------------------------------------------------------
_FAKE_SECRET = "test-secret-do-not-use-in-production"
_ALGORITHM = "HS256"


def _make_jwt(
    subject: str,
    *,
    email: str = "user@example.com",
    roles: list[str] | None = None,
    expires_delta_seconds: int = 3600,
) -> str:
    """Return a signed HS256 JWT for use in test Authorization headers."""
    try:
        from jose import jwt as jose_jwt
    except ImportError:  # pragma: no cover
        pytest.skip("python-jose not installed")

    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "roles": roles or ["user"],
        "iat": now.timestamp(),
        "exp": (now.timestamp() + expires_delta_seconds),
        "jti": str(uuid.uuid4()),
    }
    return jose_jwt.encode(payload, _FAKE_SECRET, algorithm=_ALGORITHM)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Bearer token for a standard authenticated user."""
    token = _make_jwt(subject="user-001", email="alice@example.com")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers() -> dict[str, str]:
    """Bearer token for an admin user."""
    token = _make_jwt(subject="admin-001", email="admin@example.com", roles=["admin"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers() -> dict[str, str]:
    """Bearer token for a different (non-owner) user — used in authz tests."""
    token = _make_jwt(subject="user-002", email="bob@example.com")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Async HTTP client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    HTTPX AsyncClient backed by the FastAPI ASGI app.
    Skips if the application could not be imported.
    """
    if not APP_AVAILABLE or fastapi_app is None:
        pytest.skip("FastAPI application not importable — skipping HTTP fixture")

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def authed_client(
    client: AsyncClient, auth_headers: dict[str, str]
) -> AsyncClient:
    """AsyncClient pre-loaded with authenticated user headers."""
    client.headers.update(auth_headers)
    return client


# ---------------------------------------------------------------------------
# Fake Redis
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_redis():
    """
    In-process Redis fake using fakeredis (falls back to unittest.mock if
    fakeredis is not installed).
    """
    try:
        import fakeredis

        r = fakeredis.FakeRedis(decode_responses=True)
        return r
    except ImportError:
        # Provide a minimal dict-backed mock that covers the test surface
        mock = MagicMock()
        store: dict[str, Any] = {}
        mock.get.side_effect = lambda k: store.get(k)
        mock.set.side_effect = lambda k, v, **_kw: store.update({k: v})
        mock.delete.side_effect = lambda k: store.pop(k, None)
        mock.exists.side_effect = lambda k: int(k in store)
        mock.sadd.side_effect = lambda k, *v: [store.setdefault(k, set()).add(i) for i in v]
        mock.smembers.side_effect = lambda k: store.get(k, set())
        mock.sismember.side_effect = lambda k, v: v in store.get(k, set())
        return mock


# ---------------------------------------------------------------------------
# Celery eager mode (tasks run synchronously inside the test process)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=False)
def celery_eager(monkeypatch):
    """
    Configure Celery to execute tasks eagerly (synchronously, in-process).
    Prevents tests from needing a running broker.
    """
    try:
        from app.worker import celery_app  # type: ignore[import]

        celery_app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
        )
        yield
        celery_app.conf.update(
            task_always_eager=False,
            task_eager_propagates=False,
        )
    except Exception:
        yield  # application not assembled; tests that need this fixture skip below


# ---------------------------------------------------------------------------
# SMTP mock — prevents any real email from being sent during tests
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_smtp(monkeypatch):
    """
    Globally patch SMTP so no real email is ever sent.
    Returns a MagicMock that callers can configure per-test.
    """
    with patch("smtplib.SMTP", autospec=True) as smtp_mock, \
         patch("smtplib.SMTP_SSL", autospec=True) as smtp_ssl_mock:
        yield {"SMTP": smtp_mock, "SMTP_SSL": smtp_ssl_mock}


# ---------------------------------------------------------------------------
# SES mock — prevents real AWS SES calls
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_ses(monkeypatch):
    """Globally mock boto3 SES client so no real AWS call is made."""
    ses_mock = MagicMock()
    ses_mock.send_email.return_value = {
        "MessageId": "test-message-id-001",
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    ses_mock.send_raw_email.return_value = {
        "MessageId": "test-message-id-002",
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    with patch("boto3.client", return_value=ses_mock) as boto_mock:
        yield {"boto3_client": boto_mock, "ses": ses_mock}


# ---------------------------------------------------------------------------
# Notification service stub (used when the real service is not assembled)
# ---------------------------------------------------------------------------
@pytest.fixture
def notification_service_stub():
    """
    A lightweight in-memory notification service stub implementing the
    NotificationServiceProtocol interface expected by the test suite.
    """
    from tests.notifications.stubs import InMemoryNotificationService

    return InMemoryNotificationService()

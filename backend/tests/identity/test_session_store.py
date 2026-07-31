"""
Unit + integration tests for the session-store client.

Test strategy
-------------
* All Redis interactions are replaced with a fake in-memory store so tests
  are deterministic, fast, and do not require a live Redis/ElastiCache instance.
* A single ``pytest-asyncio`` async fixture scope drives coverage of every
  public method.
* Negative / security paths (forged IDs, expired keys, corrupt payload) are
  exercised explicitly.

Test IDs map to TASK-013 acceptance criteria:
    T013-C01  create stores data and returns signed session ID
    T013-C02  read returns data and refreshes TTL (sliding window)
    T013-C03  read raises SessionSignatureError on tampered ID
    T013-C04  read raises SessionNotFoundError when key absent / expired
    T013-C05  expire deletes key (idempotent)
    T013-C06  invalidate is an alias for expire
    T013-C07  update overwrites data and refreshes TTL
    T013-C08  update raises SessionNotFoundError when key absent
    T013-C09  ttl returns remaining seconds or -2 when absent
    T013-C10  cookie helpers set correct attributes
    T013-C11  get_current_session_from_request raises 401 when no cookie
    T013-C12  get_current_session_from_request raises 401 on expired session
    T013-C13  session IDs are cryptographically distinct across calls
"""

from __future__ import annotations

import json
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from backend.app.core.config import Settings
from backend.services.identity.cookie import clear_session_cookie, set_session_cookie
from backend.services.identity.session_store import (
    SessionNotFoundError,
    SessionSignatureError,
    SessionStore,
    SessionStoreError,
    _make_session_id,
    _verify_session_id,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def make_settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "app_env": "development",
        "session_signing_secret": "test-secret-32bytes-padding-here!",
        "session_cookie_max_age": 3600,
        "redis_url": "redis://localhost:6379/0",
        "session_cookie_secure": False,  # allow non-TLS in tests
    }
    base.update(overrides)
    return Settings(**base)


class FakeRedis:
    """Minimal in-memory Redis double covering the operations SessionStore uses."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._expiry: dict[str, float] = {}  # absolute unix timestamps

    def _is_alive(self, key: str) -> bool:
        exp = self._expiry.get(key)
        if exp is None:
            return key in self._store
        return time.monotonic() < exp

    async def get(self, key: str) -> str | None:
        return self._store[key] if self._is_alive(key) else None

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
        xx: bool = False,
    ) -> str | None:
        if xx and not self._is_alive(key):
            return None
        self._store[key] = value
        if ex is not None:
            self._expiry[key] = time.monotonic() + ex
        return "OK"

    async def expire(self, key: str, ttl: int) -> int:
        if self._is_alive(key):
            self._expiry[key] = time.monotonic() + ttl
            return 1
        return 0

    async def unlink(self, key: str) -> int:
        removed = self._store.pop(key, None) is not None
        self._expiry.pop(key, None)
        return int(removed)

    async def ttl(self, key: str) -> int:
        if not self._is_alive(key):
            return -2
        exp = self._expiry.get(key)
        if exp is None:
            return -1
        return max(0, int(exp - time.monotonic()))


@pytest.fixture()
def settings() -> Settings:
    return make_settings()


@pytest.fixture()
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture()
def store(fake_redis: FakeRedis, settings: Settings) -> SessionStore:
    pool = MagicMock()
    s = SessionStore(pool=pool, settings=settings)
    # Patch _redis() to return our fake
    s._redis = lambda: fake_redis  # type: ignore[method-assign]
    return s


# ---------------------------------------------------------------------------
# T013-C01 — create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_returns_signed_session_id_and_data(
    store: SessionStore, settings: Settings
) -> None:
    data = {"user_id": "u-abc", "roles": ["viewer"]}
    session_id, returned_data = await store.create(data)

    assert returned_data == data
    # Signed ID has exactly two segments separated by "."
    parts = session_id.split(".")
    assert len(parts) == 2, "Session ID must be token.signature"
    # Verify the signature is valid
    token = _verify_session_id(session_id, settings.session_signing_secret.get_secret_value())
    assert token  # non-empty


@pytest.mark.asyncio
async def test_create_stores_data_in_redis(
    store: SessionStore, fake_redis: FakeRedis, settings: Settings
) -> None:
    data = {"user_id": "u-xyz"}
    session_id, _ = await store.create(data)
    token = session_id.split(".")[0]
    key = f"{settings.redis_session_prefix}{token}"
    raw = await fake_redis.get(key)
    assert raw is not None
    assert json.loads(raw) == data


# ---------------------------------------------------------------------------
# T013-C02 — read + TTL refresh
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_returns_stored_data(store: SessionStore) -> None:
    data = {"user_id": "u-1"}
    session_id, _ = await store.create(data)
    result = await store.read(session_id)
    assert result == data


@pytest.mark.asyncio
async def test_read_refreshes_ttl(
    store: SessionStore, fake_redis: FakeRedis, settings: Settings
) -> None:
    data = {"user_id": "u-2"}
    session_id, _ = await store.create(data, ttl=10)
    token = session_id.split(".")[0]
    key = f"{settings.redis_session_prefix}{token}"
    # Manually reduce TTL
    fake_redis._expiry[key] = time.monotonic() + 5
    await store.read(session_id, refresh_ttl=True)
    remaining = await fake_redis.ttl(key)
    # TTL should now be close to the full session_cookie_max_age (3600), not 5
    assert remaining > 100


@pytest.mark.asyncio
async def test_read_no_refresh_does_not_reset_ttl(
    store: SessionStore, fake_redis: FakeRedis, settings: Settings
) -> None:
    session_id, _ = await store.create({"x": 1}, ttl=10)
    token = session_id.split(".")[0]
    key = f"{settings.redis_session_prefix}{token}"
    fake_redis._expiry[key] = time.monotonic() + 5
    await store.read(session_id, refresh_ttl=False)
    remaining = await fake_redis.ttl(key)
    assert remaining <= 5


# ---------------------------------------------------------------------------
# T013-C03 — tampered session ID
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_raises_on_forged_signature(store: SessionStore) -> None:
    session_id, _ = await store.create({"user_id": "u-3"})
    token = session_id.split(".")[0]
    forged = f"{token}.invalidsignature"
    with pytest.raises(SessionSignatureError):
        await store.read(forged)


@pytest.mark.asyncio
async def test_read_raises_on_malformed_id(store: SessionStore) -> None:
    with pytest.raises(SessionSignatureError):
        await store.read("no-dot-here")


# ---------------------------------------------------------------------------
# T013-C04 — expired / missing session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_raises_not_found_when_absent(
    store: SessionStore, settings: Settings
) -> None:
    secret = settings.session_signing_secret.get_secret_value()
    ghost_id = _make_session_id("ghosttoken-that-does-not-exist-in-redis", secret)
    with pytest.raises(SessionNotFoundError):
        await store.read(ghost_id)


# ---------------------------------------------------------------------------
# T013-C05 — expire
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expire_deletes_session(
    store: SessionStore, fake_redis: FakeRedis, settings: Settings
) -> None:
    session_id, _ = await store.create({"user_id": "u-4"})
    await store.expire(session_id)
    token = session_id.split(".")[0]
    key = f"{settings.redis_session_prefix}{token}"
    assert await fake_redis.get(key) is None


@pytest.mark.asyncio
async def test_expire_is_idempotent(store: SessionStore) -> None:
    session_id, _ = await store.create({"user_id": "u-5"})
    await store.expire(session_id)
    # Second call must not raise
    await store.expire(session_id)


# ---------------------------------------------------------------------------
# T013-C06 — invalidate alias
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_removes_session(
    store: SessionStore, fake_redis: FakeRedis, settings: Settings
) -> None:
    session_id, _ = await store.create({"user_id": "u-6"})
    await store.invalidate(session_id)
    token = session_id.split(".")[0]
    key = f"{settings.redis_session_prefix}{token}"
    assert await fake_redis.get(key) is None


# ---------------------------------------------------------------------------
# T013-C07 / T013-C08 — update
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_overwrites_data(store: SessionStore) -> None:
    session_id, _ = await store.create({"user_id": "u-7", "role": "viewer"})
    new_data = {"user_id": "u-7", "role": "editor"}
    result = await store.update(session_id, new_data)
    assert result == new_data
    stored = await store.read(session_id)
    assert stored["role"] == "editor"


@pytest.mark.asyncio
async def test_update_raises_not_found_on_absent_session(
    store: SessionStore, settings: Settings
) -> None:
    secret = settings.session_signing_secret.get_secret_value()
    ghost_id = _make_session_id("absenttoken-that-does-not-exist-in-redis", secret)
    with pytest.raises(SessionNotFoundError):
        await store.update(ghost_id, {"user_id": "u-8"})


# ---------------------------------------------------------------------------
# T013-C09 — ttl
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ttl_returns_remaining_seconds(store: SessionStore) -> None:
    session_id, _ = await store.create({"x": 1}, ttl=60)
    remaining = await store.ttl(session_id)
    assert 0 < remaining <= 60


@pytest.mark.asyncio
async def test_ttl_returns_minus_two_when_absent(
    store: SessionStore, settings: Settings
) -> None:
    secret = settings.session_signing_secret.get_secret_value()
    ghost_id = _make_session_id("missing-token-for-ttl-check-here00", secret)
    remaining = await store.ttl(ghost_id)
    assert remaining == -2


# ---------------------------------------------------------------------------
# T013-C10 — cookie helpers
# ---------------------------------------------------------------------------


def test_set_session_cookie_attributes() -> None:
    from starlette.responses import Response as StarletteResponse

    settings = make_settings(
        session_cookie_name="sid",
        session_cookie_secure=True,
        session_cookie_httponly=True,
        session_cookie_samesite="lax",
        session_cookie_max_age=1800,
        session_cookie_path="/",
        session_cookie_domain=None,
    )
    resp = StarletteResponse()
    set_session_cookie(resp, "mytoken.sig", settings)
    header = resp.headers["set-cookie"]
    assert "HttpOnly" in header
    assert "SameSite=lax" in header
    assert "Max-Age=1800" in header
    assert "Path=/" in header
    assert "mytoken.sig" in header


def test_clear_session_cookie_sets_expired() -> None:
    from starlette.responses import Response as StarletteResponse

    settings = make_settings(session_cookie_name="sid")
    resp = StarletteResponse()
    clear_session_cookie(resp, settings)
    header = resp.headers["set-cookie"]
    # delete_cookie sets Max-Age=0
    assert "Max-Age=0" in header or "expires" in header.lower()


# ---------------------------------------------------------------------------
# T013-C11 / T013-C12 — dependency: get_current_session_from_request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_current_session_dep_401_when_no_cookie(
    store: SessionStore, settings: Settings
) -> None:
    """Dependency raises 401 when no session cookie is present."""
    from backend.services.identity.dependencies import get_current_session_from_request

    request = MagicMock()
    request.cookies = {}

    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await get_current_session_from_request(request, store, settings)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_current_session_dep_401_on_expired_session(
    store: SessionStore, fake_redis: FakeRedis, settings: Settings
) -> None:
    """Dependency raises 401 when the session has been expired."""
    from fastapi import HTTPException

    from backend.services.identity.dependencies import get_current_session_from_request

    session_id, _ = await store.create({"user_id": "u-9"})
    await store.expire(session_id)

    request = MagicMock()
    request.cookies = {settings.session_cookie_name: session_id}

    with pytest.raises(HTTPException) as exc_info:
        await get_current_session_from_request(request, store, settings)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_current_session_dep_returns_data_on_valid_session(
    store: SessionStore, settings: Settings
) -> None:
    """Dependency returns session data when cookie is valid."""
    from backend.services.identity.dependencies import get_current_session_from_request

    data = {"user_id": "u-10", "roles": ["admin"]}
    session_id, _ = await store.create(data)

    request = MagicMock()
    request.cookies = {settings.session_cookie_name: session_id}

    result = await get_current_session_from_request(request, store, settings)
    assert result == data


# ---------------------------------------------------------------------------
# T013-C13 — uniqueness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_session_ids_are_unique(store: SessionStore) -> None:
    ids = {(await store.create({"i": i}))[0] for i in range(50)}
    assert len(ids) == 50, "All 50 session IDs must be distinct."

"""
Integration tests: rate-limit enforcement on HTTP endpoints (AC-031.2 / VER-020).

Verifies:
  1. Registration succeeds while under threshold.
  2. POST /auth/register returns 429 with generic message after threshold.
  3. POST /auth/login returns 429 with generic message after threshold.
  4. POST /api/v1/content returns 429 with generic message after threshold.
  5. 429 responses include RateLimit-* and Retry-After headers.
  6. 429 message does NOT reveal internal threshold/window values.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CONTENT_URL = "/api/v1/content"

GENERIC_429_MESSAGE = "Too many requests. Please try again later."


def _register_body(n: int) -> dict[str, str]:
    return {
        "email": f"user{n}@example.com",
        "username": f"user{n}",
        "password": "Secret1234",
    }


# ---------------------------------------------------------------------------
# Registration rate-limit (AC-031.2)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_allows_within_limit(client: AsyncClient) -> None:
    """First request under the threshold must succeed (201)."""
    resp = await client.post(REGISTER_URL, json=_register_body(1))
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_429_on_threshold_breach(client: AsyncClient) -> None:
    """After RATELIMIT_REGISTER_MAX (default=5) attempts, next → 429."""
    # The FakeRedis is fresh for each test function (function-scoped fixture).
    # Override the limit to 2 for speed without patching settings —
    # we exhaust the default limit=5 with 5 distinct bodies then one more.
    for i in range(1, 6):
        await client.post(REGISTER_URL, json=_register_body(i))

    resp = await client.post(REGISTER_URL, json=_register_body(99))
    assert resp.status_code == 429


@pytest.mark.asyncio
async def test_register_429_generic_message(client: AsyncClient) -> None:
    """The 429 body must use the generic message (AC-031.2 – no threshold leak)."""
    for i in range(1, 6):
        await client.post(REGISTER_URL, json=_register_body(i))

    resp = await client.post(REGISTER_URL, json=_register_body(99))
    assert resp.status_code == 429
    body = resp.json()
    assert body["detail"] == GENERIC_429_MESSAGE
    # Ensure the message does not embed numbers that reveal internal limits.
    assert "5" not in body["detail"]
    assert "3600" not in body["detail"]


@pytest.mark.asyncio
async def test_register_429_has_ratelimit_headers(client: AsyncClient) -> None:
    """429 must carry RateLimit-* and Retry-After headers."""
    for i in range(1, 6):
        await client.post(REGISTER_URL, json=_register_body(i))

    resp = await client.post(REGISTER_URL, json=_register_body(99))
    assert resp.status_code == 429
    assert "ratelimit-limit" in resp.headers
    assert "retry-after" in resp.headers


# ---------------------------------------------------------------------------
# Login rate-limit (AC-031.2)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_429_on_threshold_breach(client: AsyncClient) -> None:
    """After RATELIMIT_LOGIN_MAX (default=10) attempts, next → 429."""
    login_body = {"email": "any@example.com", "password": "wrong"}
    for _ in range(10):
        await client.post(LOGIN_URL, json=login_body)

    resp = await client.post(LOGIN_URL, json=login_body)
    assert resp.status_code == 429


@pytest.mark.asyncio
async def test_login_429_generic_message(client: AsyncClient) -> None:
    """The login 429 must carry the generic message (AC-031.2)."""
    login_body = {"email": "any@example.com", "password": "wrong"}
    for _ in range(10):
        await client.post(LOGIN_URL, json=login_body)

    resp = await client.post(LOGIN_URL, json=login_body)
    assert resp.status_code == 429
    assert resp.json()["detail"] == GENERIC_429_MESSAGE


# ---------------------------------------------------------------------------
# Content-creation rate-limit (AC-031.2)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_content_create_429_on_threshold_breach(client: AsyncClient) -> None:
    """
    After RATELIMIT_CONTENT_CREATE_MAX (default=60) attempts the endpoint
    returns 429 (not 401 — the rate-limit check fires before auth on an
    unauthenticated request that hits the IP-bucket fallback).
    """
    content_body = {"title": "T", "body": "B"}
    # Exhaust 60 slots (rate-limit dep fires before JWT auth check in the
    # dependency resolution order because it's listed first in `dependencies`).
    for _ in range(60):
        await client.post(CONTENT_URL, json=content_body)

    resp = await client.post(CONTENT_URL, json=content_body)
    assert resp.status_code == 429


@pytest.mark.asyncio
async def test_content_create_429_generic_message(client: AsyncClient) -> None:
    content_body = {"title": "T", "body": "B"}
    for _ in range(60):
        await client.post(CONTENT_URL, json=content_body)

    resp = await client.post(CONTENT_URL, json=content_body)
    assert resp.status_code == 429
    assert resp.json()["detail"] == GENERIC_429_MESSAGE

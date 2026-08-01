"""HTTP integration tests for POST /api/v1/auth/login.

Tests verify the router translates service outcomes into correct
HTTP status codes and generic response bodies.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.identity.models import User


# ---------------------------------------------------------------------------
# AC-003: HTTP-level generic responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    """AC-003.1 — Unknown email → 401 with generic body."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["detail"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(
    client: AsyncClient, active_user: User
) -> None:
    """AC-003.2 — Wrong password → 401 with same generic body."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "wrong"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["detail"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_generic_failure_bodies_are_identical(
    client: AsyncClient, active_user: User
) -> None:
    """AC-003.3 — Both failure modes return identical code + message (no enumeration)."""
    r1 = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "bad"},
    )
    r2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "bad"},
    )
    assert r1.json()["detail"]["code"] == r2.json()["detail"]["code"]
    assert r1.json()["detail"]["message"] == r2.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_login_missing_email_returns_422(client: AsyncClient) -> None:
    """Malformed request → 422 Unprocessable Entity."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"password": "only-password"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_empty_password_returns_422(client: AsyncClient) -> None:
    """Empty password string → 422 (fails min_length=1 constraint)."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": ""},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# AC-004: Account-status HTTP codes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_locked_account_returns_423(
    client: AsyncClient, locked_user: User
) -> None:
    """AC-004.1 — Locked account → 423 Locked."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": locked_user.email, "password": "correct-password"},
    )
    assert resp.status_code == 423
    assert resp.json()["detail"]["code"] == "account_locked"


@pytest.mark.asyncio
async def test_suspended_account_returns_403(
    client: AsyncClient, suspended_user: User
) -> None:
    """AC-004.2 — Suspended account → 403 Forbidden."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": suspended_user.email, "password": "correct-password"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "account_inactive"


@pytest.mark.asyncio
async def test_unverified_account_returns_403(
    client: AsyncClient, unverified_user: User
) -> None:
    """AC-004.3 — Unverified account → 403 Forbidden."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": unverified_user.email, "password": "correct-password"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "account_inactive"


# ---------------------------------------------------------------------------
# AC-004: Happy paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_login_returns_200_with_token(
    client: AsyncClient, active_user: User
) -> None:
    """AC-004.7 — Valid credentials → 200 with access_token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "correct-password"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


@pytest.mark.asyncio
async def test_mfa_user_returns_200_with_challenge(
    client: AsyncClient, totp_user: User
) -> None:
    """AC-004.9 — MFA-enabled user → 200 with challenge_token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": totp_user.email, "password": "correct-password"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["mfa_required"] is True
    assert body["challenge_token"]
    assert body["mfa_method"] == "totp"
    assert "expires_at" in body


@pytest.mark.asyncio
async def test_response_never_contains_password_hash(
    client: AsyncClient, active_user: User
) -> None:
    """Security — response body must not leak password_hash."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "correct-password"},
    )
    assert "password_hash" not in resp.text
    assert "password" not in resp.text

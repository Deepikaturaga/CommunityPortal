"""Tests for email verification endpoints — TASK-016 / COMP-001.

Covers:
- POST /api/v1/auth/verify-email  (token consumption)
- POST /api/v1/auth/resend-verification  (resend / anti-enumeration)
- Service-layer unit tests (expired, already-used, superseded)
- VER-012: anti-enumeration on resend endpoint
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.services.identity.verify import (
    TokenExpiredError,
    TokenNotFoundError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
    consume_verification_token,
    issue_verification_token,
    resend_verification_token,
)

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
RESEND_URL = "/api/v1/auth/resend-verification"

VALID_REGISTER = {
    "email": "alice@example.com",
    "password": "Str0ng!Pass#2024",
    "full_name": "Alice Smith",
}

# Sentinel used in place of a real bcrypt hash in direct DB fixture tests.
_FAKE_HASH = "not-a-real-hash"  # noqa: S105


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register_and_get_token(
    client: AsyncClient,
    db: AsyncSession,
) -> tuple[str, EmailVerificationToken]:
    """Register a user and return the raw token string + first token row."""
    resp = await client.post(REGISTER_URL, json=VALID_REGISTER)
    assert resp.status_code == 201
    stmt = select(EmailVerificationToken)
    result = await db.execute(stmt)
    token_row = result.scalars().first()
    assert token_row is not None
    return token_row.token, token_row


# ── Token issuance ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_registration_creates_token_row(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Registering a user persists exactly one EmailVerificationToken row."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    stmt = select(EmailVerificationToken)
    result = await db_session.execute(stmt)
    rows = result.scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_token_has_future_expiry(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The issued token's expires_at is in the future."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    stmt = select(EmailVerificationToken)
    result = await db_session.execute(stmt)
    token_row = result.scalars().first()
    assert token_row is not None
    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    assert expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_token_is_not_consumed_on_issuance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Freshly issued token has consumed_at = NULL."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    stmt = select(EmailVerificationToken)
    result = await db_session.execute(stmt)
    token_row = result.scalars().first()
    assert token_row is not None
    assert token_row.consumed_at is None


# ── Happy path: verify email ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_email_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Valid token → HTTP 200."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_verify_email_response_body(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Valid token → response contains email and success message."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert "verified" in body["message"].lower()


@pytest.mark.asyncio
async def test_verify_email_marks_user_verified(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """After a successful verify, user.is_verified is True."""
    raw_token, token_row = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    stmt = select(User).where(User.id == token_row.user_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_verify_email_marks_token_consumed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """After consumption the token row has consumed_at set."""
    raw_token, token_row = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.id == token_row.id
    )
    result = await db_session.execute(stmt)
    refreshed = result.scalar_one_or_none()
    assert refreshed is not None
    assert refreshed.consumed_at is not None


# ── 410 Gone: already used ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_already_used_returns_410(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Using the same token twice → HTTP 410."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_verify_already_used_error_code(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Second use → error code is token_invalid."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    errors = resp.json()["errors"]
    assert any(e["code"] == "token_invalid" for e in errors)


# ── 410 Gone: expired token (service unit test) ───────────────────────────────


@pytest.mark.asyncio
async def test_verify_expired_token_raises(
    db_session: AsyncSession,
) -> None:
    """Service raises TokenExpiredError when expires_at is in the past."""
    user = User(
        email="bob@example.com",
        password_hash=_FAKE_HASH,
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    past = datetime.now(UTC) - timedelta(hours=1)
    token_obj = EmailVerificationToken(
        user_id=user.id,
        expires_at=past,
    )
    db_session.add(token_obj)
    await db_session.flush()
    with pytest.raises(TokenExpiredError):
        await consume_verification_token(db_session, token_obj.token)


# ── 410 Gone: superseded token ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_superseded_token_returns_410(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Token superseded by resend → HTTP 410."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    # Resend issues a new token, superseding the old one
    await client.post(RESEND_URL, json={"email": "alice@example.com"})
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    assert resp.status_code == 410


# ── 404: unknown token ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_unknown_token_returns_404(client: AsyncClient) -> None:
    """Non-existent token → HTTP 404."""
    resp = await client.post(VERIFY_URL, json={"token": "totally-made-up-token"})
    assert resp.status_code == 404


# ── Service: TokenNotFoundError ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_service_raises_token_not_found(db_session: AsyncSession) -> None:
    """consume_verification_token raises TokenNotFoundError for garbage input."""
    with pytest.raises(TokenNotFoundError):
        await consume_verification_token(db_session, "no-such-token")


# ── Service: supersede_existing ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_issue_supersedes_previous_tokens(db_session: AsyncSession) -> None:
    """Issuing a second token marks the first one superseded."""
    user = User(
        email="carol@example.com",
        password_hash=_FAKE_HASH,
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    first = await issue_verification_token(db_session, user)
    _second = await issue_verification_token(db_session, user)
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.id == first.id
    )
    result = await db_session.execute(stmt)
    refreshed = result.scalar_one_or_none()
    assert refreshed is not None
    assert refreshed.superseded is True


# ── Resend: happy path ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resend_returns_200(client: AsyncClient) -> None:
    """POST /resend-verification always returns 200."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    resp = await client.post(RESEND_URL, json={"email": "alice@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_resend_creates_new_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Resend creates a second token row for the user."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    await client.post(RESEND_URL, json={"email": "alice@example.com"})
    stmt = select(EmailVerificationToken)
    result = await db_session.execute(stmt)
    rows = result.scalars().all()
    assert len(rows) == 2  # original + resent


@pytest.mark.asyncio
async def test_resend_supersedes_old_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """After resend the original token is superseded."""
    _, first_row = await _register_and_get_token(client, db_session)
    await client.post(RESEND_URL, json={"email": "alice@example.com"})
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.id == first_row.id
    )
    result = await db_session.execute(stmt)
    refreshed = result.scalar_one_or_none()
    assert refreshed is not None
    assert refreshed.superseded is True


# ── VER-012: anti-enumeration on resend ──────────────────────────────────────


@pytest.mark.asyncio
async def test_resend_unknown_email_returns_200(client: AsyncClient) -> None:
    """VER-012: unknown email on resend still returns 200 (anti-enumeration)."""
    resp = await client.post(RESEND_URL, json={"email": "nobody@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_resend_already_verified_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """VER-012: already-verified email returns 200 (anti-enumeration)."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    resp = await client.post(RESEND_URL, json={"email": "alice@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_resend_response_body_indistinguishable(client: AsyncClient) -> None:
    """VER-012: response bodies for unknown and known emails are identical."""
    resp_known = await client.post(RESEND_URL, json={"email": "alice@example.com"})
    resp_unknown = await client.post(RESEND_URL, json={"email": "ghost@example.com"})
    assert resp_known.json() == resp_unknown.json()


# ── Resend: service layer ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_service_resend_raises_user_not_found(
    db_session: AsyncSession,
) -> None:
    """resend_verification_token raises UserNotFoundError for unknown email."""
    with pytest.raises(UserNotFoundError):
        await resend_verification_token(db_session, "ghost@example.com")


@pytest.mark.asyncio
async def test_service_resend_raises_already_verified(
    db_session: AsyncSession,
) -> None:
    """resend_verification_token raises UserAlreadyVerifiedError for verified users."""
    user = User(
        email="verified@example.com",
        password_hash=_FAKE_HASH,
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    with pytest.raises(UserAlreadyVerifiedError):
        await resend_verification_token(db_session, "verified@example.com")


# ── Input validation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_missing_token_returns_422(client: AsyncClient) -> None:
    """Missing token field → HTTP 422."""
    resp = await client.post(VERIFY_URL, json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_resend_invalid_email_returns_422(client: AsyncClient) -> None:
    """Malformed email on resend → HTTP 422."""
    resp = await client.post(RESEND_URL, json={"email": "not-an-email"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_resend_email_normalised(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Resend accepts mixed-case email and normalises it."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    resp = await client.post(RESEND_URL, json={"email": "ALICE@EXAMPLE.COM"})
    assert resp.status_code == 200

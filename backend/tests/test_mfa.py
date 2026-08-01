"""Tests for POST /api/v1/auth/mfa/verify (TASK-019, VER-016).

Coverage
--------
* VER-016-1  Valid TOTP code + valid challenge -> 200 + access_token
* VER-016-2  Invalid OTP code -> 401 generic
* VER-016-3  Expired challenge (DB expiry) -> 401
* VER-016-3b Expired challenge (signed token expiry) -> 401
* VER-016-4  Tampered / garbage challenge token -> 401 generic
* VER-016-5  Already-consumed challenge -> 401 (replay prevention)
* VER-016-6  Missing fields -> 422
* VER-016-7  Response never leaks totp_secret or password_hash
* VER-016-8  LoginAttempt row written for failure (audit)
* VER-016-9  LoginAttempt row written for success (audit)
* VER-016-10 EMAIL_OTP method returns 401 (not yet implemented, safe rejection)
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pyotp
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.identity.login import InvalidCredentials, _issue_mfa_challenge_token
from app.services.identity.mfa import (
    MFA_EXPIRED_CODE,
    MFA_INVALID_CODE,
    _verify_totp,
)
from app.services.identity.models import (
    AccountStatus,
    LoginAttempt,
    MFAChallenge,
    MFAMethod,
    User,
)

# ---------------------------------------------------------------------------
# Additional fixtures
# ---------------------------------------------------------------------------

_TOTP_SECRET = pyotp.random_base32()


@pytest_asyncio.fixture
async def totp_user_with_secret(db_session: AsyncSession) -> User:
    """Active TOTP-enabled user with a known secret stored in the DB."""
    import bcrypt  # type: ignore[import-untyped]

    pw_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt(rounds=4)).decode()
    user = User(
        id=uuid.uuid4(),
        email="mfa-totp@example.com",
        password_hash=pw_hash,
        full_name="MFA Tester",
        status=AccountStatus.ACTIVE,
        mfa_method=MFAMethod.TOTP,
        mfa_enabled=True,
        totp_secret=_TOTP_SECRET,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def email_otp_user(db_session: AsyncSession) -> User:
    """Active EMAIL_OTP-enabled user."""
    import bcrypt  # type: ignore[import-untyped]

    pw_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt(rounds=4)).decode()
    user = User(
        id=uuid.uuid4(),
        email="mfa-email@example.com",
        password_hash=pw_hash,
        full_name="Email OTP Tester",
        status=AccountStatus.ACTIVE,
        mfa_method=MFAMethod.EMAIL_OTP,
        mfa_enabled=True,
        totp_secret=None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _store_challenge(
    db_session: AsyncSession,
    user: User,
    *,
    expires_in: int = 300,
    consumed: bool = False,
) -> str:
    """Issue + persist a challenge token for a given user, return the token."""
    token, expires_at = _issue_mfa_challenge_token(user.id)
    if expires_in <= 0:
        expires_at = datetime.now(UTC) - timedelta(seconds=1)
    challenge = MFAChallenge(
        user_id=user.id,
        challenge_token=token,
        expires_at=expires_at,
        consumed=consumed,
    )
    db_session.add(challenge)
    await db_session.commit()
    return token


# ---------------------------------------------------------------------------
# Unit-level helper tests
# ---------------------------------------------------------------------------


def test_verify_totp_valid() -> None:
    """_verify_totp returns True for the current TOTP code."""
    code = pyotp.TOTP(_TOTP_SECRET).now()
    assert _verify_totp(_TOTP_SECRET, code) is True


def test_verify_totp_wrong_code() -> None:
    """_verify_totp returns False for a clearly wrong code."""
    assert _verify_totp(_TOTP_SECRET, "000000") is False


def test_verify_totp_malformed_code() -> None:
    """_verify_totp returns False (not raises) for non-numeric garbage."""
    assert _verify_totp(_TOTP_SECRET, "BADCODE!!!") is False


def test_verify_totp_bad_secret() -> None:
    """_verify_totp returns False (not raises) when the secret is malformed."""
    assert _verify_totp("NOT-A-VALID-BASE32!!!", "123456") is False


# ---------------------------------------------------------------------------
# VER-016-1  Happy path -- valid TOTP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_totp_returns_200_and_access_token(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-1 -- Valid OTP + valid challenge -> 200 with access_token."""
    token = await _store_challenge(db_session, totp_user_with_secret)
    code = pyotp.TOTP(_TOTP_SECRET).now()

    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": code},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"  # noqa: S105
    assert body["expires_in"] > 0


# ---------------------------------------------------------------------------
# VER-016-2  Invalid OTP -> 401 generic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_otp_returns_401(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-2 -- Wrong OTP code -> 401 generic error."""
    token = await _store_challenge(db_session, totp_user_with_secret)

    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": "000000"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == MFA_INVALID_CODE


# ---------------------------------------------------------------------------
# VER-016-3  Expired challenge (DB expiry) -> 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expired_challenge_returns_401(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-3 -- Expired challenge (past DB expires_at) -> 401."""
    token = await _store_challenge(db_session, totp_user_with_secret)
    code = pyotp.TOTP(_TOTP_SECRET).now()

    # Force the stored row's expires_at into the past
    await db_session.execute(
        update(MFAChallenge)
        .where(MFAChallenge.challenge_token == token)
        .values(expires_at=datetime.now(UTC) - timedelta(seconds=10))
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": code},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] in (MFA_EXPIRED_CODE, "mfa_challenge_expired")


# ---------------------------------------------------------------------------
# VER-016-3b Expired challenge (signed token expiry) -> 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_signed_token_expiry_returns_401(
    client: AsyncClient,
) -> None:
    """VER-016-3b -- Signed challenge token expiry -> 401.

    Patches verify_mfa_challenge_token directly so the itsdangerous
    SignatureExpired path is exercised without needing real clock
    manipulation or lru_cache busting.
    """
    with patch(
        "app.services.identity.mfa.verify_mfa_challenge_token",
        side_effect=InvalidCredentials("mfa_challenge_expired", "MFA challenge has expired."),
    ):
        resp = await client.post(
            "/api/v1/auth/mfa/verify",
            json={"challenge_token": "any.token.value", "otp_code": "123456"},
        )
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"]["code"]


# ---------------------------------------------------------------------------
# VER-016-4  Tampered / garbage token -> 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tampered_challenge_token_returns_401(
    client: AsyncClient,
) -> None:
    """VER-016-4 -- Garbage / tampered challenge_token -> 401."""
    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": "this.is.not.valid", "otp_code": "123456"},
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"]["code"]


# ---------------------------------------------------------------------------
# VER-016-5  Replay prevention -- already-consumed challenge
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_consumed_challenge_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-5 -- Re-submitting a consumed challenge -> 401 (single-use)."""
    token = await _store_challenge(db_session, totp_user_with_secret, consumed=True)
    code = pyotp.TOTP(_TOTP_SECRET).now()

    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": code},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_double_submit_second_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-5b -- Second call with the same token after a success -> 401."""
    token = await _store_challenge(db_session, totp_user_with_secret)
    code = pyotp.TOTP(_TOTP_SECRET).now()

    r1 = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": code},
    )
    assert r1.status_code == 200

    r2 = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": code},
    )
    assert r2.status_code == 401


# ---------------------------------------------------------------------------
# VER-016-6  Missing fields -> 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_otp_code_returns_422(client: AsyncClient) -> None:
    """VER-016-6a -- Missing otp_code -> 422."""
    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": "some-token"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_missing_challenge_token_returns_422(client: AsyncClient) -> None:
    """VER-016-6b -- Missing challenge_token -> 422."""
    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"otp_code": "123456"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_empty_otp_code_returns_422(client: AsyncClient) -> None:
    """VER-016-6c -- Empty string for otp_code -> 422 (min_length=1)."""
    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": "some-token", "otp_code": ""},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# VER-016-7  Response never leaks secrets
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_success_response_does_not_leak_secrets(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-7 -- totp_secret and password_hash must not appear in responses."""
    token = await _store_challenge(db_session, totp_user_with_secret)
    code = pyotp.TOTP(_TOTP_SECRET).now()

    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": code},
    )
    assert resp.status_code == 200
    assert "totp_secret" not in resp.text
    assert "password_hash" not in resp.text
    assert _TOTP_SECRET not in resp.text


@pytest.mark.asyncio
async def test_failure_response_does_not_leak_secrets(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-7b -- Error responses must not leak internal detail."""
    token = await _store_challenge(db_session, totp_user_with_secret)

    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": "000000"},
    )
    assert resp.status_code == 401
    assert "totp_secret" not in resp.text
    assert "password_hash" not in resp.text
    assert _TOTP_SECRET not in resp.text


# ---------------------------------------------------------------------------
# VER-016-8  Audit log -- failure writes LoginAttempt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_failed_mfa_writes_audit_row(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-8 -- Failed OTP -> LoginAttempt row with success=False."""
    token = await _store_challenge(db_session, totp_user_with_secret)

    await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": "000000"},
    )

    result = await db_session.execute(
        select(LoginAttempt).where(
            LoginAttempt.user_id == totp_user_with_secret.id,
            LoginAttempt.success.is_(False),
            LoginAttempt.detail == "mfa_bad_otp",
        )
    )
    assert len(result.scalars().all()) >= 1


# ---------------------------------------------------------------------------
# VER-016-9  Audit log -- success writes LoginAttempt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_mfa_writes_audit_row(
    client: AsyncClient,
    db_session: AsyncSession,
    totp_user_with_secret: User,
) -> None:
    """VER-016-9 -- Successful MFA verify -> LoginAttempt row with success=True."""
    token = await _store_challenge(db_session, totp_user_with_secret)
    code = pyotp.TOTP(_TOTP_SECRET).now()

    await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": code},
    )

    result = await db_session.execute(
        select(LoginAttempt).where(
            LoginAttempt.user_id == totp_user_with_secret.id,
            LoginAttempt.success.is_(True),
            LoginAttempt.detail == "mfa_success",
        )
    )
    assert len(result.scalars().all()) >= 1


# ---------------------------------------------------------------------------
# VER-016-10  EMAIL_OTP safely rejected (not implemented)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_email_otp_method_returns_401(
    client: AsyncClient,
    db_session: AsyncSession,
    email_otp_user: User,
) -> None:
    """VER-016-10 -- EMAIL_OTP method -> 401 (not yet implemented, safe rejection)."""
    token = await _store_challenge(db_session, email_otp_user)

    resp = await client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_token": token, "otp_code": "123456"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == MFA_INVALID_CODE

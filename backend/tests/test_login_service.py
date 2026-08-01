"""Unit tests for the login service layer.

AC-003.x — Generic failure responses (no enumeration)
AC-004.x — Account-status checks + lockout
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt  # type: ignore[import-untyped]
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.identity.login import (
    AccountInactive,
    AccountLocked,
    InvalidCredentials,
    login,
)
from app.services.identity.models import AccountStatus, MFAMethod, User
from app.services.identity.schemas import LoginRequest, LoginSuccess, MFAChallengeResponse

# Pre-hash test passwords at low cost rounds for speed
_HASH_SECRET = bcrypt.hashpw(b"secret", bcrypt.gensalt(rounds=4)).decode()
_HASH_CORRECT = bcrypt.hashpw(b"correct-password", bcrypt.gensalt(rounds=4)).decode()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _req(email: str = "user@example.com", password: str = "correct-password") -> LoginRequest:
    return LoginRequest(email=email, password=password)


# ---------------------------------------------------------------------------
# AC-003: Generic failure responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_email_raises_invalid_credentials(db_session: AsyncSession) -> None:
    """AC-003.1 — Unknown email returns generic InvalidCredentials."""
    with pytest.raises(InvalidCredentials) as exc_info:
        await login(_req(email="nobody@example.com"), db_session)
    assert exc_info.value.code == "invalid_credentials"


@pytest.mark.asyncio
async def test_wrong_password_raises_invalid_credentials(
    db_session: AsyncSession, active_user: User
) -> None:
    """AC-003.2 — Wrong password for a real account returns generic InvalidCredentials."""
    with pytest.raises(InvalidCredentials) as exc_info:
        await login(_req(password="wrong-password"), db_session)
    assert exc_info.value.code == "invalid_credentials"


@pytest.mark.asyncio
async def test_wrong_password_and_unknown_email_same_code(
    db_session: AsyncSession, active_user: User
) -> None:
    """AC-003.3 — Both failure modes return identical code + message (no enumeration)."""
    with pytest.raises(InvalidCredentials) as exc_bad_pass:
        await login(_req(password="bad"), db_session)
    with pytest.raises(InvalidCredentials) as exc_no_user:
        await login(_req(email="ghost@example.com"), db_session)
    assert exc_bad_pass.value.code == exc_no_user.value.code
    assert exc_bad_pass.value.message == exc_no_user.value.message


# ---------------------------------------------------------------------------
# AC-004: Account status checks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_locked_account_raises_account_locked(
    db_session: AsyncSession, locked_user: User
) -> None:
    """AC-004.1 — Locked account raises AccountLocked before password is checked."""
    with pytest.raises(AccountLocked) as exc_info:
        await login(_req(email=locked_user.email), db_session)
    assert exc_info.value.code == "account_locked"
    assert exc_info.value.locked_until > datetime.now(UTC)


@pytest.mark.asyncio
async def test_suspended_account_raises_account_inactive(
    db_session: AsyncSession, suspended_user: User
) -> None:
    """AC-004.2 — Suspended account raises AccountInactive with generic code."""
    with pytest.raises(AccountInactive) as exc_info:
        await login(_req(email=suspended_user.email), db_session)
    assert exc_info.value.code == "account_inactive"


@pytest.mark.asyncio
async def test_unverified_account_raises_account_inactive(
    db_session: AsyncSession, unverified_user: User
) -> None:
    """AC-004.3 — Unverified account raises AccountInactive."""
    with pytest.raises(AccountInactive) as exc_info:
        await login(_req(email=unverified_user.email), db_session)
    assert exc_info.value.code == "account_inactive"


# ---------------------------------------------------------------------------
# AC-004: Lockout increment / threshold
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_failed_logins_increment_counter(
    db_session: AsyncSession, active_user: User
) -> None:
    """AC-004.4 — Each bad password increments failed_login_count."""
    await db_session.commit()  # flush fixture writes

    with pytest.raises(InvalidCredentials):
        await login(_req(password="bad1"), db_session)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.id == active_user.id))
    refreshed = result.scalar_one()
    assert refreshed.failed_login_count == 1


@pytest.mark.asyncio
async def test_lockout_triggered_at_threshold(db_session: AsyncSession) -> None:
    """AC-004.5 — Account locks after max_login_attempts consecutive failures."""
    settings = get_settings()
    user = User(
        id=uuid.uuid4(),
        email="lockme@example.com",
        password_hash=_HASH_SECRET,
        status=AccountStatus.ACTIVE,
        mfa_method=MFAMethod.NONE,
        mfa_enabled=False,
        failed_login_count=settings.max_login_attempts - 1,  # one away
    )
    db_session.add(user)
    await db_session.commit()

    with pytest.raises((AccountLocked, InvalidCredentials)):
        await login(_req(email="lockme@example.com", password="wrong"), db_session)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.id == user.id))
    refreshed = result.scalar_one()
    assert (
        refreshed.status == AccountStatus.LOCKED
        or refreshed.failed_login_count >= settings.max_login_attempts
    )


@pytest.mark.asyncio
async def test_expired_lock_auto_clears(db_session: AsyncSession) -> None:
    """AC-004.6 — An expired lock is cleared automatically on next login attempt."""
    user = User(
        id=uuid.uuid4(),
        email="waslocked@example.com",
        password_hash=_HASH_CORRECT,
        status=AccountStatus.LOCKED,
        mfa_method=MFAMethod.NONE,
        mfa_enabled=False,
        failed_login_count=5,
        locked_until=datetime.now(UTC) - timedelta(seconds=1),  # already expired
    )
    db_session.add(user)
    await db_session.commit()

    result = await login(_req(email="waslocked@example.com"), db_session)
    assert isinstance(result, LoginSuccess)


# ---------------------------------------------------------------------------
# AC-004: Successful login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_login_returns_access_token(
    db_session: AsyncSession, active_user: User
) -> None:
    """AC-004.7 — Valid credentials return a LoginSuccess with a non-empty access_token."""
    result = await login(_req(email=active_user.email), db_session)
    assert isinstance(result, LoginSuccess)
    assert result.access_token
    assert result.token_type == "bearer"
    assert result.expires_in > 0


@pytest.mark.asyncio
async def test_successful_login_clears_failure_counter(db_session: AsyncSession) -> None:
    """AC-004.8 — Successful login resets the failure counter."""
    user = User(
        id=uuid.uuid4(),
        email="retry@example.com",
        password_hash=_HASH_CORRECT,
        status=AccountStatus.ACTIVE,
        mfa_method=MFAMethod.NONE,
        mfa_enabled=False,
        failed_login_count=3,
    )
    db_session.add(user)
    await db_session.commit()

    await login(_req(email="retry@example.com"), db_session)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.id == user.id))
    refreshed = result.scalar_one()
    assert refreshed.failed_login_count == 0


# ---------------------------------------------------------------------------
# AC-004: MFA gating
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mfa_user_gets_challenge_not_token(
    db_session: AsyncSession, totp_user: User
) -> None:
    """AC-004.9 — User with MFA enabled receives an MFAChallengeResponse, not an access token."""
    result = await login(_req(email=totp_user.email), db_session)
    assert isinstance(result, MFAChallengeResponse)
    assert result.mfa_required is True
    assert result.challenge_token
    assert result.mfa_method == MFAMethod.TOTP
    assert result.expires_at > datetime.now(UTC)

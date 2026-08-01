"""Tests for TASK-018: lockout policy, progressive delay, and owner alert.

Acceptance criteria verified
-----------------------------
AC-018.1  Lockout triggers at ``max_login_attempts`` threshold.
AC-018.2  ``locked_until`` is set and status flips to LOCKED in the DB.
AC-018.3  Owner alert (alerter) is called exactly once on lock.
AC-018.4  Alert is NOT called for failures below the threshold.
AC-018.5  Progressive delay schedule is respected (non-zero for attempt ≥ 2).
AC-018.6  Delay is capped by ``lockout_delay_max_seconds``.
AC-018.7  Alerter errors are swallowed — lock still persists.
AC-018.8  apply_failure returns None below threshold, datetime at threshold.

VER-001: Negative-path HTTP tests (bad credential / deactivated → generic 401)
---------------------------------------------------------------------------
VER-001.1  Unknown email → 401 ``invalid_credentials``
VER-001.2  Wrong password → 401 ``invalid_credentials``
VER-001.3  Deactivated account → 401 ``invalid_credentials`` (generic, not 403)
VER-001.4  Both bad-cred failures return identical code + message
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import bcrypt  # type: ignore[import-untyped]
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.identity.lockout import _delay_for_attempt, apply_failure
from app.services.identity.models import AccountStatus, MFAMethod, User

_HASH_CORRECT = bcrypt.hashpw(b"correct-password", bcrypt.gensalt(rounds=4)).decode()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _active_user(email: str = "locktest@example.com", count: int = 0) -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        password_hash=_HASH_CORRECT,
        status=AccountStatus.ACTIVE,
        mfa_method=MFAMethod.NONE,
        mfa_enabled=False,
        failed_login_count=count,
    )


def _deactivated_user(email: str = "dead@example.com") -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        password_hash=_HASH_CORRECT,
        status=AccountStatus.DEACTIVATED,
        mfa_method=MFAMethod.NONE,
        mfa_enabled=False,
        failed_login_count=0,
    )


# ---------------------------------------------------------------------------
# VER-001: Negative-path HTTP tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ver001_unknown_email_returns_401_generic(client: AsyncClient) -> None:
    """VER-001.1 — Unknown email → 401 with generic invalid_credentials code."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "anything"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_ver001_wrong_password_returns_401_generic(
    client: AsyncClient, active_user: User
) -> None:
    """VER-001.2 — Wrong password → 401 with generic invalid_credentials code."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_ver001_deactivated_account_returns_401_generic(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """VER-001.3 — Deactivated account → generic 401 (not 403, avoids enumeration)."""
    user = _deactivated_user()
    db_session.add(user)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "correct-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_ver001_bad_cred_bodies_are_identical(
    client: AsyncClient, active_user: User
) -> None:
    """VER-001.4 — Unknown email and wrong password return identical code + message."""
    r_bad_pass = await client.post(
        "/api/v1/auth/login",
        json={"email": active_user.email, "password": "bad"},
    )
    r_no_user = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "bad"},
    )
    assert r_bad_pass.json()["detail"]["code"] == r_no_user.json()["detail"]["code"]
    assert r_bad_pass.json()["detail"]["message"] == r_no_user.json()["detail"]["message"]


# ---------------------------------------------------------------------------
# AC-018: apply_failure unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac018_returns_none_below_threshold(db_session: AsyncSession) -> None:
    """AC-018.8 — apply_failure returns None when count is still below threshold."""
    user = _active_user(count=0)  # attempt 1 of N — still below threshold
    db_session.add(user)
    await db_session.commit()

    with patch("app.services.identity.lockout.asyncio.sleep", new_callable=AsyncMock):
        result = await apply_failure(db_session, user)

    assert result is None


@pytest.mark.asyncio
async def test_ac018_returns_locked_until_at_threshold(db_session: AsyncSession) -> None:
    """AC-018.8 — apply_failure returns a future datetime when threshold is hit."""
    settings = get_settings()
    user = _active_user(count=settings.max_login_attempts - 1)
    db_session.add(user)
    await db_session.commit()

    with patch("app.services.identity.lockout.asyncio.sleep", new_callable=AsyncMock):
        locked_until = await apply_failure(db_session, user)

    after = datetime.now(UTC)
    assert locked_until is not None
    assert locked_until > after


@pytest.mark.asyncio
async def test_ac018_db_status_locked_at_threshold(db_session: AsyncSession) -> None:
    """AC-018.1 + AC-018.2 — Status flips to LOCKED and locked_until is persisted."""
    settings = get_settings()
    user = _active_user(count=settings.max_login_attempts - 1)
    db_session.add(user)
    await db_session.commit()

    with patch("app.services.identity.lockout.asyncio.sleep", new_callable=AsyncMock):
        await apply_failure(db_session, user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.id == user.id))
    refreshed = result.scalar_one()
    assert refreshed.status == AccountStatus.LOCKED
    assert refreshed.locked_until is not None
    assert refreshed.failed_login_count == settings.max_login_attempts


@pytest.mark.asyncio
async def test_ac018_alerter_called_on_lock(db_session: AsyncSession) -> None:
    """AC-018.3 — Alerter is called exactly once when the account locks."""
    settings = get_settings()
    user = _active_user(count=settings.max_login_attempts - 1)
    db_session.add(user)
    await db_session.commit()

    alerter = AsyncMock()
    with patch("app.services.identity.lockout.asyncio.sleep", new_callable=AsyncMock):
        await apply_failure(db_session, user, ip_address="1.2.3.4", alerter=alerter)

    alerter.assert_awaited_once()
    _call_args, call_kwargs = alerter.call_args
    assert call_kwargs.get("ip_address") == "1.2.3.4" or (
        len(_call_args) >= 4 and _call_args[3] == "1.2.3.4"
    )


@pytest.mark.asyncio
async def test_ac018_alerter_not_called_below_threshold(db_session: AsyncSession) -> None:
    """AC-018.4 — Alerter is NOT called when failure count stays below threshold."""
    user = _active_user(count=0)
    db_session.add(user)
    await db_session.commit()

    alerter = AsyncMock()
    with patch("app.services.identity.lockout.asyncio.sleep", new_callable=AsyncMock):
        await apply_failure(db_session, user, alerter=alerter)

    alerter.assert_not_awaited()


@pytest.mark.asyncio
async def test_ac018_alerter_error_is_swallowed(db_session: AsyncSession) -> None:
    """AC-018.7 — A crashing alerter must not prevent the lock from being written."""
    settings = get_settings()
    user = _active_user(count=settings.max_login_attempts - 1)
    db_session.add(user)
    await db_session.commit()

    async def _bad_alerter(**_kwargs: object) -> None:
        raise RuntimeError("alert service down")

    with patch("app.services.identity.lockout.asyncio.sleep", new_callable=AsyncMock):
        locked_until = await apply_failure(db_session, user, alerter=_bad_alerter)  # type: ignore[arg-type]

    assert locked_until is not None
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.id == user.id))
    refreshed = result.scalar_one()
    assert refreshed.status == AccountStatus.LOCKED


# ---------------------------------------------------------------------------
# AC-018: Progressive delay schedule (pure unit — no DB)
# ---------------------------------------------------------------------------


def test_ac018_delay_schedule_zero_for_first_attempt() -> None:
    """AC-018.5 — First attempt carries no delay."""
    assert _delay_for_attempt(1, max_seconds=10.0) == 0.0


def test_ac018_delay_schedule_nonzero_from_second_attempt() -> None:
    """AC-018.5 — Delay is non-zero for attempt ≥ 2."""
    assert _delay_for_attempt(2, max_seconds=10.0) > 0.0
    assert _delay_for_attempt(3, max_seconds=10.0) > 0.0


def test_ac018_delay_capped_by_max() -> None:
    """AC-018.6 — Delay never exceeds lockout_delay_max_seconds."""
    cap = 1.0
    for attempt in range(1, 10):
        assert _delay_for_attempt(attempt, max_seconds=cap) <= cap


def test_ac018_delay_schedule_monotonic() -> None:
    """AC-018.5 — Delay is non-decreasing as attempt count grows."""
    delays = [_delay_for_attempt(i, max_seconds=100.0) for i in range(1, 8)]
    assert delays == sorted(delays)


@pytest.mark.asyncio
async def test_ac018_sleep_is_called_on_second_attempt(db_session: AsyncSession) -> None:
    """AC-018.5 — asyncio.sleep is called with a positive value on attempt 2."""
    user = _active_user(count=1)  # count=1 means this will be attempt 2
    db_session.add(user)
    await db_session.commit()

    sleep_mock = AsyncMock()
    with patch("app.services.identity.lockout.asyncio.sleep", sleep_mock):
        await apply_failure(db_session, user)

    sleep_mock.assert_awaited_once()
    (delay,), _ = sleep_mock.call_args
    assert delay > 0.0


# ---------------------------------------------------------------------------
# AC-018: HTTP-level lockout flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ac018_http_lockout_after_threshold_failures(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """AC-018.1 — Repeated bad-password POSTs trigger 423 after threshold.

    The conftest ``client`` fixture now commits the session even on
    HTTPException so that failure counter increments survive across requests.
    """
    settings = get_settings()
    user = _active_user(email="hammered@example.com", count=0)
    db_session.add(user)
    await db_session.commit()

    responses: list[int] = []
    with patch("app.services.identity.lockout.asyncio.sleep", new_callable=AsyncMock):
        for _ in range(settings.max_login_attempts):
            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "hammered@example.com", "password": "wrong"},
            )
            responses.append(resp.status_code)

    # The final attempt at threshold must produce 423
    assert 423 in responses, f"Expected 423 in {responses}"


@pytest.mark.asyncio
async def test_ac018_locked_account_returns_423_immediately(
    client: AsyncClient, locked_user: User
) -> None:
    """AC-018.1 — Already-locked account returns 423 without checking password."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": locked_user.email, "password": "correct-password"},
    )
    assert resp.status_code == 423
    assert resp.json()["detail"]["code"] == "account_locked"

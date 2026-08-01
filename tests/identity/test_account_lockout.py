"""
tests/identity/test_account_lockout.py
----------------------------------------
VER-017: Account lockout after repeated failed login attempts.

Policy under test (from TEST_SETTINGS)
---------------------------------------
* max_failed_login_attempts = 5
* lockout_duration_seconds  = 900  (15 minutes)

Scenarios
---------
1. Failed attempts increment the counter.
2. Reaching the threshold triggers a lockout (locked_until set).
3. Locked account returns 429 even with correct credentials.
4. Successful login resets the failure counter.
5. An already-locked user (fixture) is immediately blocked.
6. After lockout expires (simulate via DB manipulation) login succeeds.
7. Failed TOTP attempts count toward lockout.
8. Error response for a locked account does NOT leak the lockout timestamp
   or failure count.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS, _make_user


class TestLockoutAccrual:
    @pytest.mark.asyncio
    async def test_failed_login_increments_counter(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """Each failed password attempt must increment failed_login_attempts."""
        initial = plain_user.failed_login_attempts

        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "WrongPass1!"},
        )
        await db_session.refresh(plain_user)
        assert plain_user.failed_login_attempts == initial + 1

    @pytest.mark.asyncio
    async def test_multiple_failures_accumulate(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """3 consecutive failures must yield failed_login_attempts == 3."""
        for _ in range(3):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )
        await db_session.refresh(plain_user)
        assert plain_user.failed_login_attempts == 3

    @pytest.mark.asyncio
    async def test_reaching_threshold_sets_locked_until(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """Hitting max_failed_login_attempts must set locked_until in the future."""
        threshold = TEST_SETTINGS.max_failed_login_attempts
        now_before = datetime.now(tz=timezone.utc)

        for _ in range(threshold):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )
        await db_session.refresh(plain_user)

        assert plain_user.locked_until is not None
        locked = (
            plain_user.locked_until.replace(tzinfo=timezone.utc)
            if plain_user.locked_until.tzinfo is None
            else plain_user.locked_until
        )
        assert locked > now_before, "locked_until must be in the future"

    @pytest.mark.asyncio
    async def test_locked_account_returns_429(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """After threshold failures, even a correct password must return 429."""
        threshold = TEST_SETTINGS.max_failed_login_attempts
        for _ in range(threshold):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )

        # Now try with CORRECT credentials
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 429, (
            "Locked account must return 429 even with correct credentials"
        )

    @pytest.mark.asyncio
    async def test_lockout_response_does_not_leak_internal_details(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """Error response must not expose locked_until timestamp or attempt count."""
        threshold = TEST_SETTINGS.max_failed_login_attempts
        for _ in range(threshold):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        body_str = resp.text
        # Must not expose the actual locked_until datetime or attempt count
        assert "locked_until" not in body_str
        assert "failed_login_attempts" not in body_str

    @pytest.mark.asyncio
    async def test_successful_login_resets_counter(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """A successful login must reset failed_login_attempts to 0."""
        # Accumulate 2 failures (below threshold)
        for _ in range(2):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )
        await db_session.refresh(plain_user)
        assert plain_user.failed_login_attempts == 2

        # Successful login
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        await db_session.refresh(plain_user)
        assert plain_user.failed_login_attempts == 0


class TestLockoutFixtures:
    @pytest.mark.asyncio
    async def test_pre_locked_user_immediately_blocked(
        self, client: AsyncClient, locked_user: User
    ) -> None:
        """A user with locked_until in the future must be rejected immediately."""
        resp = await client.post(
            "/auth/login",
            json={"email": locked_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_expired_lockout_allows_login(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """When locked_until is in the past, login must succeed again."""
        # Create a user whose lockout has already expired
        expired_lock = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        user = await _make_user(
            db_session,
            email="expired-lock@example.com",
            failed_attempts=5,
            locked_until=expired_lock,
        )
        resp = await client.post(
            "/auth/login",
            json={"email": user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200, (
            "Login must succeed after the lockout period has expired"
        )

    @pytest.mark.asyncio
    async def test_expired_lockout_resets_counter_on_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Successful post-expiry login must also clear the failure counter."""
        expired_lock = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        user = await _make_user(
            db_session,
            email="expired-reset@example.com",
            failed_attempts=5,
            locked_until=expired_lock,
        )
        await client.post(
            "/auth/login",
            json={"email": user.email, "password": "Password1!"},
        )
        await db_session.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


class TestTOTPLockout:
    @pytest.mark.asyncio
    async def test_failed_totp_counts_toward_lockout(
        self, client: AsyncClient, mfa_user: User, db_session: AsyncSession
    ) -> None:
        """Failed TOTP attempts must increment the lockout counter."""
        initial = mfa_user.failed_login_attempts

        await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": "000000",
            },
        )
        await db_session.refresh(mfa_user)
        assert mfa_user.failed_login_attempts == initial + 1

    @pytest.mark.asyncio
    async def test_mfa_lockout_threshold_triggers_block(
        self, client: AsyncClient, mfa_user: User, db_session: AsyncSession
    ) -> None:
        """Repeated TOTP failures must eventually lock the account."""
        threshold = TEST_SETTINGS.max_failed_login_attempts

        for _ in range(threshold):
            await client.post(
                "/auth/login",
                json={
                    "email": mfa_user.email,
                    "password": "Password1!",
                    "totp_code": "000000",
                },
            )

        import pyotp

        valid_code = pyotp.TOTP(mfa_user.totp_secret or "").now()
        resp = await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": valid_code,
            },
        )
        # Even valid TOTP cannot bypass a lockout
        assert resp.status_code == 429

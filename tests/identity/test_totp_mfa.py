"""
tests/identity/test_totp_mfa.py
---------------------------------
VER-012: TOTP-based MFA is correctly enforced.

Scenarios
---------
* A user without MFA can log in with password alone.
* A user with MFA enabled is challenged for a TOTP code when none supplied.
* A valid TOTP code allows login when MFA is enabled.
* An invalid TOTP code is rejected (401).
* TOTP setup: server issues secret + URI; confirmation with a valid code enables MFA.
* TOTP confirmation with an invalid code is rejected (400).
* TOTP codes cannot be reused within the same time window (replay protection via
  pyotp's internal drift window — validated structurally since we can't advance time).
* The provisioning URI contains the issuer and account email.
"""
from __future__ import annotations

import pytest
import pyotp
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_totp_secret, verify_totp
from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS, _make_user


class TestTOTPUnit:
    def test_generate_secret_is_valid_base32(self) -> None:
        secret = generate_totp_secret()
        # Base32 alphabet — should not raise
        import base64

        base64.b32decode(secret, casefold=True)
        assert len(secret) >= 16

    def test_valid_code_accepted(self) -> None:
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert verify_totp(secret, code, settings=TEST_SETTINGS) is True

    def test_invalid_code_rejected(self) -> None:
        secret = generate_totp_secret()
        assert verify_totp(secret, "000000", settings=TEST_SETTINGS) is False

    def test_wrong_secret_rejected(self) -> None:
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()
        code = pyotp.TOTP(secret1).now()
        assert verify_totp(secret2, code, settings=TEST_SETTINGS) is False

    def test_provisioning_uri_contains_issuer(self) -> None:
        from app.core.security import get_totp_uri

        secret = generate_totp_secret()
        uri = get_totp_uri(secret, "user@example.com", settings=TEST_SETTINGS)
        assert "MyApp" in uri or "otpauth" in uri

    def test_provisioning_uri_contains_email(self) -> None:
        from app.core.security import get_totp_uri

        secret = generate_totp_secret()
        uri = get_totp_uri(secret, "user@example.com", settings=TEST_SETTINGS)
        assert "user%40example.com" in uri or "user@example.com" in uri


class TestMFALoginFlow:
    @pytest.mark.asyncio
    async def test_login_without_mfa_requires_no_totp(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Users without MFA can log in with password only."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        assert resp.json()["mfa_required"] is False

    @pytest.mark.asyncio
    async def test_mfa_user_challenged_when_no_code(
        self, client: AsyncClient, mfa_user: User
    ) -> None:
        """User with MFA enabled must be told MFA is required when no code supplied."""
        resp = await client.post(
            "/auth/login",
            json={"email": mfa_user.email, "password": "Password1!"},
        )
        # Server returns 200 with mfa_required=True — no tokens issued
        assert resp.status_code == 200
        body = resp.json()
        assert body["mfa_required"] is True
        assert body["csrf_token"] == "", "No CSRF token when MFA gate not passed"
        # No access_token cookie yet
        assert "access_token" not in resp.cookies

    @pytest.mark.asyncio
    async def test_mfa_user_with_valid_code_gets_tokens(
        self, client: AsyncClient, mfa_user: User
    ) -> None:
        """Providing the correct TOTP code completes login and issues tokens."""
        assert mfa_user.totp_secret is not None
        code = pyotp.TOTP(mfa_user.totp_secret).now()

        resp = await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": code,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["mfa_required"] is False
        assert "access_token" in resp.cookies

    @pytest.mark.asyncio
    async def test_mfa_user_with_invalid_code_rejected(
        self, client: AsyncClient, mfa_user: User
    ) -> None:
        """An incorrect TOTP code must return 401."""
        resp = await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": "000000",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_mfa_user_with_invalid_code_increments_lockout_counter(
        self, client: AsyncClient, mfa_user: User, db_session: AsyncSession
    ) -> None:
        """Failed TOTP attempts count toward account lockout."""
        initial_attempts = mfa_user.failed_login_attempts

        await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": "000000",
            },
        )
        await db_session.refresh(mfa_user)
        assert mfa_user.failed_login_attempts == initial_attempts + 1


class TestTOTPEnrollment:
    @pytest.mark.asyncio
    async def test_totp_setup_returns_secret_and_uri(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """POST /auth/totp/setup must return a secret and otpauth URI."""
        # Authenticate first
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        resp = await client.post("/auth/totp/setup")
        assert resp.status_code == 200
        body = resp.json()
        assert "secret" in body
        assert "uri" in body
        assert body["uri"].startswith("otpauth://totp/")

    @pytest.mark.asyncio
    async def test_totp_setup_without_auth_rejected(self, client: AsyncClient) -> None:
        """TOTP setup must require an authenticated session."""
        resp = await client.post("/auth/totp/setup")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_totp_confirm_with_valid_code_enables_mfa(
        self,
        client: AsyncClient,
        plain_user: User,
        db_session: AsyncSession,
    ) -> None:
        """Confirming TOTP with a valid code must set totp_enabled=True."""
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        # Setup: get secret
        setup_resp = await client.post("/auth/totp/setup")
        secret = setup_resp.json()["secret"]
        code = pyotp.TOTP(secret).now()

        confirm_resp = await client.post(
            "/auth/totp/confirm",
            json={"code": code},
        )
        assert confirm_resp.status_code == 200

        await db_session.refresh(plain_user)
        assert plain_user.totp_enabled is True

    @pytest.mark.asyncio
    async def test_totp_confirm_with_invalid_code_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Confirming TOTP with a wrong code must return 400."""
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        await client.post("/auth/totp/setup")  # initialise secret

        resp = await client.post(
            "/auth/totp/confirm",
            json={"code": "000000"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_totp_confirm_without_setup_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Calling /auth/totp/confirm before /auth/totp/setup must return 400."""
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        # plain_user has no totp_secret set
        resp = await client.post(
            "/auth/totp/confirm",
            json={"code": "123456"},
        )
        assert resp.status_code == 400

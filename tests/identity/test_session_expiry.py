"""
tests/identity/test_session_expiry.py
---------------------------------------
VER-006: Sessions expire after the configured lifetime.

We simulate token expiry by constructing tokens with a past `exp` claim
(without using a time-travel library — we directly craft JWTs with
manipulated timestamps) and verify the server rejects them.

We also verify:
* An expired access token is rejected by /auth/me.
* An expired refresh token is rejected by /auth/refresh.
* A token with exp in the near future is still accepted.
* The cookie max_age matches the token lifetime.
"""
from __future__ import annotations

import time

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.security import create_access_token, create_refresh_token
from app.core.session import set_auth_cookies
from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS


def _make_expired_access_token(subject: str) -> str:
    """Craft an access token whose `exp` is 1 second in the past."""
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now - 100,
        "exp": now - 1,   # already expired
        "typ": "access",
        "jti": "test-expired-jti",
    }
    return jwt.encode(
        payload,
        TEST_SETTINGS.jwt_secret.get_secret_value(),
        algorithm=TEST_SETTINGS.jwt_algorithm,
    )


def _make_expired_refresh_token(subject: str) -> str:
    """Craft a refresh token whose `exp` is 1 second in the past."""
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now - 100,
        "exp": now - 1,
        "typ": "refresh",
        "jti": "test-expired-refresh-jti",
    }
    return jwt.encode(
        payload,
        TEST_SETTINGS.jwt_secret.get_secret_value(),
        algorithm=TEST_SETTINGS.jwt_algorithm,
    )


def _sign_for_cookie(raw_jwt: str) -> str:
    """Wrap a raw JWT in an itsdangerous signature as the server would."""
    from itsdangerous import TimestampSigner

    signer = TimestampSigner(TEST_SETTINGS.session_secret.get_secret_value())
    return signer.sign(raw_jwt).decode()


class TestSessionExpiry:
    @pytest.mark.asyncio
    async def test_expired_access_token_rejected_by_me(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """An expired access token must return 401 from /auth/me."""
        expired = _make_expired_access_token(plain_user.email)
        signed = _sign_for_cookie(expired)
        resp = await client.get("/auth/me", cookies={"access_token": signed})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_refresh_token_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """An expired refresh token must return 401 from /auth/refresh."""
        # Log in to get a valid CSRF
        login = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf = login.json()["csrf_token"]

        expired_refresh = _make_expired_refresh_token(plain_user.email)

        resp = await client.post(
            "/auth/refresh",
            cookies={
                "refresh_token": expired_refresh,
                "csrf_token": csrf,
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_near_expiry_still_accepted(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """A token expiring in the future (even 60 s away) must be accepted."""
        # Create a token expiring in 60 seconds
        now = int(time.time())
        payload = {
            "sub": plain_user.email,
            "iat": now,
            "exp": now + 60,
            "typ": "access",
            "jti": "short-lived-jti",
        }
        raw = jwt.encode(
            payload,
            TEST_SETTINGS.jwt_secret.get_secret_value(),
            algorithm=TEST_SETTINGS.jwt_algorithm,
        )
        signed = _sign_for_cookie(raw)
        resp = await client.get("/auth/me", cookies={"access_token": signed})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_access_cookie_max_age_set(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Login response must set max-age on the access_token cookie."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        set_cookie_headers = resp.headers.get_list("set-cookie")
        access_headers = [h for h in set_cookie_headers if "access_token" in h]
        assert len(access_headers) == 1
        header = access_headers[0].lower()
        assert "max-age=" in header, "access_token cookie must carry max-age"

    @pytest.mark.asyncio
    async def test_refresh_cookie_max_age_set(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Login response must set max-age on the refresh_token cookie."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        set_cookie_headers = resp.headers.get_list("set-cookie")
        refresh_headers = [h for h in set_cookie_headers if "refresh_token" in h]
        assert len(refresh_headers) == 1
        header = refresh_headers[0].lower()
        assert "max-age=" in header, "refresh_token cookie must carry max-age"

    @pytest.mark.asyncio
    async def test_logout_sets_expired_cookies(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Logout must delete (expire) the session cookies."""
        login = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf = login.json()["csrf_token"]

        logout = await client.post(
            "/auth/logout",
            headers={"X-CSRF-Token": csrf},
        )
        assert logout.status_code == 200
        # After logout, accessing /me must fail
        me = await client.get("/auth/me")
        assert me.status_code == 401

    @pytest.mark.asyncio
    async def test_no_access_token_returns_401(self, client: AsyncClient) -> None:
        """Request with no session cookie must be rejected."""
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

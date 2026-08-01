"""
tests/identity/test_session_fixation.py
-----------------------------------------
VER-005: Session fixation is prevented.

The server must NEVER accept or extend a pre-existing session cookie
value handed in by the client.  On every successful authentication:
  * A brand-new access_token cookie value is issued.
  * A brand-new CSRF token is issued.
  * An old, pre-login cookie is not honoured for protected endpoints
    if it was not issued by the server.

Attack model
------------
An attacker who knows a victim's session cookie value (e.g. obtained before
login via a cross-site trick) must not be able to ride the victim's session
post-authentication.  Because our tokens are server-issued JWTs (not client-
specified IDs), the attack surface does not exist at the protocol level —
but we verify the server always regenerates tokens on login.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestSessionFixationPrevention:
    @pytest.mark.asyncio
    async def test_fresh_token_issued_on_each_login(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Two sequential logins must produce distinct access_token cookie values."""
        resp1 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        token1 = resp1.cookies.get("access_token")

        resp2 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        token2 = resp2.cookies.get("access_token")

        assert token1 is not None
        assert token2 is not None
        assert token1 != token2, (
            "Server must issue a new token on each login — old value must not persist"
        )

    @pytest.mark.asyncio
    async def test_fresh_csrf_issued_on_each_login(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Each login must produce a distinct CSRF token."""
        resp1 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf1 = resp1.json().get("csrf_token")

        resp2 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf2 = resp2.json().get("csrf_token")

        assert csrf1 and csrf2
        assert csrf1 != csrf2, "CSRF token must be regenerated on each login"

    @pytest.mark.asyncio
    async def test_attacker_injected_cookie_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """A fabricated/unsigned access_token cookie must be rejected by /auth/me."""
        # Attacker constructs a raw JWT without the itsdangerous signature
        from app.core.security import create_access_token
        from tests.identity.conftest import TEST_SETTINGS

        raw_jwt = create_access_token(plain_user.email, settings=TEST_SETTINGS)

        # Inject directly as cookie (missing the itsdangerous signature wrapper)
        resp = await client.get(
            "/auth/me",
            cookies={"access_token": raw_jwt},
        )
        assert resp.status_code == 401, (
            "Unsigned/raw JWT must be rejected — the server only accepts itsdangerous-signed cookies"
        )

    @pytest.mark.asyncio
    async def test_forged_session_cookie_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """A completely fabricated cookie value must be rejected."""
        resp = await client.get(
            "/auth/me",
            cookies={"access_token": "not.a.real.token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_old_token_not_automatically_extended(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Accessing /auth/me with a valid token does not silently re-issue tokens."""
        # Log in
        login_resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert login_resp.status_code == 200
        original_token = login_resp.cookies.get("access_token")

        # Call /me
        me_resp = await client.get("/auth/me")
        assert me_resp.status_code == 200

        # The /me endpoint must NOT re-issue tokens — no new set-cookie
        set_cookie_headers = me_resp.headers.get_list("set-cookie")
        token_cookies = [h for h in set_cookie_headers if "access_token" in h]
        assert len(token_cookies) == 0, (
            "/auth/me must not silently re-issue access_token cookies — that would widen the fixation window"
        )

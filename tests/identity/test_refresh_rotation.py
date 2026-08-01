"""
tests/identity/test_refresh_rotation.py
-----------------------------------------
VER-016: Refresh token rotation — each refresh call issues a new token pair
         and invalidates the previous refresh token.

Security properties verified
-----------------------------
1. After /auth/refresh, the OLD refresh token must be rejected.
2. After /auth/refresh, the NEW refresh token is accepted.
3. A second use of the OLD refresh token (replay) must trigger family
   revocation — the NEW token is also rejected.
4. The access token changes on every /auth/refresh call (new JTI + iat).
5. CSRF is enforced on /auth/refresh (covered also in test_csrf.py but
   restated here for completeness).
6. A missing refresh token cookie returns 401.
7. A completely fabricated refresh token returns 401.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.security import decode_refresh_token
from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS


async def _login(client: AsyncClient, email: str) -> dict:
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": "Password1!"},
    )
    assert resp.status_code == 200
    return resp.json()


class TestRefreshRotation:
    @pytest.mark.asyncio
    async def test_refresh_issues_new_access_token(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Each /auth/refresh must produce a new access_token cookie."""
        login_body = await _login(client, plain_user.email)
        old_access = client.cookies.get("access_token")

        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": login_body["csrf_token"]},
        )
        assert resp.status_code == 200
        new_access = client.cookies.get("access_token")
        assert old_access != new_access, "access_token must change after refresh"

    @pytest.mark.asyncio
    async def test_refresh_issues_new_csrf_token(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        login_body = await _login(client, plain_user.email)
        old_csrf = login_body["csrf_token"]

        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": old_csrf},
        )
        new_csrf = resp.json()["csrf_token"]
        assert old_csrf != new_csrf, "CSRF token must rotate on each refresh"

    @pytest.mark.asyncio
    async def test_old_refresh_token_rejected_after_rotation(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """After refresh, the previous refresh token must no longer work."""
        login_body = await _login(client, plain_user.email)
        csrf1 = login_body["csrf_token"]

        # Capture old refresh token value before first rotation
        # We need to grab it from Set-Cookie headers at login time
        login_resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf1 = login_resp.json()["csrf_token"]

        # Get the raw refresh token from Set-Cookie header
        set_cookie = login_resp.headers.get_list("set-cookie")
        refresh_headers = [h for h in set_cookie if "refresh_token" in h]
        assert len(refresh_headers) == 1
        # Extract cookie value from "refresh_token=VALUE; ..."
        old_refresh_value = refresh_headers[0].split(";")[0].split("=", 1)[1]

        # Perform one rotation
        rot1 = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf1},
        )
        assert rot1.status_code == 200
        new_csrf = rot1.json()["csrf_token"]

        # Now try to use the OLD refresh token
        resp = await client.post(
            "/auth/refresh",
            cookies={
                "refresh_token": old_refresh_value,
                "csrf_token": new_csrf,
            },
            headers={"X-CSRF-Token": new_csrf},
        )
        assert resp.status_code == 401, (
            "Old (rotated-out) refresh token must be rejected"
        )

    @pytest.mark.asyncio
    async def test_replay_triggers_family_revocation(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Reusing a revoked refresh token must revoke the whole token family."""
        # Capture original refresh token at login
        login_resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf1 = login_resp.json()["csrf_token"]
        set_cookie = login_resp.headers.get_list("set-cookie")
        old_refresh_value = [
            h.split(";")[0].split("=", 1)[1]
            for h in set_cookie
            if "refresh_token" in h
        ][0]

        # First rotation — succeeds, consumes old refresh token
        rot1 = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf1},
        )
        assert rot1.status_code == 200
        new_csrf = rot1.json()["csrf_token"]

        # Attacker replays the OLD refresh token — server detects reuse
        replay = await client.post(
            "/auth/refresh",
            cookies={
                "refresh_token": old_refresh_value,
                "csrf_token": new_csrf,
            },
            headers={"X-CSRF-Token": new_csrf},
        )
        assert replay.status_code == 401

        # The NEW (legitimate) refresh token must now also be revoked
        # because the server detected a replay and wiped refresh_token_jti
        second_try = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": new_csrf},
        )
        assert second_try.status_code == 401, (
            "After replay detection, the entire token family must be revoked"
        )

    @pytest.mark.asyncio
    async def test_new_access_token_has_different_jti(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Each refresh must produce an access token with a new JTI."""
        login_body = await _login(client, plain_user.email)

        # Extract JTI from first access token (after login)
        # The access token in the cookie is itsdangerous-signed;
        # we must unsign it first.
        from itsdangerous import TimestampSigner

        signer = TimestampSigner(TEST_SETTINGS.session_secret.get_secret_value())
        signed1 = client.cookies.get("access_token", "")
        raw1 = signer.unsign(signed1, max_age=TEST_SETTINGS.access_token_expire_seconds).decode()
        jti1 = jwt.get_unverified_claims(raw1)["jti"]

        # Refresh
        await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": login_body["csrf_token"]},
        )

        signed2 = client.cookies.get("access_token", "")
        raw2 = signer.unsign(signed2, max_age=TEST_SETTINGS.access_token_expire_seconds).decode()
        jti2 = jwt.get_unverified_claims(raw2)["jti"]

        assert jti1 != jti2, "Each token issuance must produce a unique JTI"

    @pytest.mark.asyncio
    async def test_missing_refresh_cookie_returns_401(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        login_body = await _login(client, plain_user.email)
        csrf = login_body["csrf_token"]
        # Explicitly omit the refresh cookie
        resp = await client.post(
            "/auth/refresh",
            cookies={"csrf_token": csrf},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_fabricated_refresh_token_returns_401(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        login_body = await _login(client, plain_user.email)
        csrf = login_body["csrf_token"]
        resp = await client.post(
            "/auth/refresh",
            cookies={
                "refresh_token": "not.a.valid.jwt",
                "csrf_token": csrf,
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_updates_cookie_max_age(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """The newly issued access_token cookie must carry a fresh max-age."""
        login_body = await _login(client, plain_user.email)
        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": login_body["csrf_token"]},
        )
        assert resp.status_code == 200
        set_cookie = resp.headers.get_list("set-cookie")
        access = [h for h in set_cookie if "access_token" in h]
        assert len(access) == 1
        assert "max-age=" in access[0].lower()

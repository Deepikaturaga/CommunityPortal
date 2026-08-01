"""
JRN-002: Login and Token Management Journey
Happy path + key alternates:
  - HP: Valid credentials → 200, access + refresh tokens
  - HP2: OAuth2 form login (/token endpoint)
  - HP3: Refresh token rotates both tokens
  - ALT-1: Wrong password → 403
  - ALT-2: Non-existent email → 403
  - ALT-3: Deactivated account → 403
  - ALT-4: Access /users/me without token → 401
  - ALT-5: Access /users/me with valid token → 200
  - ALT-6: Profile update via PUT /users/me
  - ALT-7: Password change
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import _create_user, auth_headers


@pytest.mark.asyncio
class TestJRN002Login:
    async def _register(self, client: AsyncClient, suffix: str = "x") -> dict:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"login{suffix}@example.com",
                "username": f"loginuser{suffix}",
                "display_name": "Login User",
                "password": "Password1",
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def test_hp_login_returns_tokens(self, client: AsyncClient) -> None:
        await self._register(client, "a")
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "logina@example.com", "password": "Password1"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_hp2_oauth2_form_login(self, client: AsyncClient) -> None:
        await self._register(client, "b")
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "loginb@example.com", "password": "Password1"},
        )
        assert resp.status_code == 200, resp.text
        assert "access_token" in resp.json()

    async def test_hp3_refresh_rotates_tokens(self, client: AsyncClient) -> None:
        await self._register(client, "c")
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "loginc@example.com", "password": "Password1"},
        )
        refresh_token = login.json()["refresh_token"]
        original_access = login.json()["access_token"]

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        # tokens must be new
        assert body["access_token"] != original_access

    async def test_alt1_wrong_password_returns_403(self, client: AsyncClient) -> None:
        await self._register(client, "d")
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "logind@example.com", "password": "WrongPass9"},
        )
        assert resp.status_code == 403

    async def test_alt2_nonexistent_email_returns_403(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Password1"},
        )
        assert resp.status_code == 403

    async def test_alt3_deactivated_account_returns_403(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user = await _create_user(
            db_session,
            email="inactive@example.com",
            username="inactive1",
            is_active=False,
        )
        await db_session.commit()
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "Password1"},
        )
        assert resp.status_code == 403

    async def test_alt4_no_token_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_alt5_valid_token_returns_me(
        self, client: AsyncClient, member_user, member_headers
    ) -> None:
        resp = await client.get("/api/v1/users/me", headers=member_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == member_user.email

    async def test_alt6_profile_update(
        self, client: AsyncClient, member_user, member_headers
    ) -> None:
        resp = await client.put(
            "/api/v1/users/me",
            headers=member_headers,
            json={"display_name": "New Name", "bio": "Hello world"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["display_name"] == "New Name"
        assert body["bio"] == "Hello world"

    async def test_alt7_password_change(
        self, client: AsyncClient, member_user, member_headers
    ) -> None:
        resp = await client.post(
            "/api/v1/users/me/change-password",
            headers=member_headers,
            json={"current_password": "Password1", "new_password": "NewPass99"},
        )
        assert resp.status_code == 204
        # should now be able to login with new password
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": member_user.email, "password": "NewPass99"},
        )
        assert login.status_code == 200

    async def test_invalid_refresh_token_returns_403(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "completely.invalid.token"},
        )
        assert resp.status_code == 403

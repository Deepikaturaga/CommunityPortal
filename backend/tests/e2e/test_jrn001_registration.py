"""
JRN-001: User Registration Journey
Happy path + key alternates:
  - HP: Register with valid data → 201, user object returned
  - ALT-1: Duplicate email → 409
  - ALT-2: Duplicate username → 409
  - ALT-3: Weak password (no digit) → 422
  - ALT-4: Invalid email format → 422
  - ALT-5: Short username → 422
  - ALT-6: Profile visible after registration (GET /users/{id})
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestJRN001Registration:
    async def test_hp_register_returns_201_with_user(self, client: AsyncClient) -> None:
        """HP: successful registration returns 201 and user payload."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "username": "alice",
                "display_name": "Alice Smith",
                "password": "Secure1pass",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["email"] == "alice@example.com"
        assert body["username"] == "alice"
        assert body["display_name"] == "Alice Smith"
        assert body["role"] == "member"
        assert body["is_active"] is True
        # password must not be exposed
        assert "password" not in body
        assert "hashed_password" not in body

    async def test_hp_registered_user_gets_an_id(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bob@example.com",
                "username": "bob99",
                "display_name": "Bob",
                "password": "Bobpass1",
            },
        )
        assert resp.status_code == 201
        assert isinstance(resp.json()["id"], int)

    async def test_alt1_duplicate_email_returns_409(self, client: AsyncClient) -> None:
        payload = {
            "email": "dup@example.com",
            "username": "unique1",
            "display_name": "User",
            "password": "Password1",
        }
        r1 = await client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201
        payload["username"] = "unique2"
        r2 = await client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409

    async def test_alt2_duplicate_username_returns_409(self, client: AsyncClient) -> None:
        payload = {
            "email": "first@example.com",
            "username": "sameuser",
            "display_name": "User",
            "password": "Password1",
        }
        r1 = await client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201
        payload["email"] = "second@example.com"
        r2 = await client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409

    async def test_alt3_password_without_digit_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "nodigit@example.com",
                "username": "nodigit",
                "display_name": "User",
                "password": "NoDigitHere",
            },
        )
        assert resp.status_code == 422

    async def test_alt4_invalid_email_format_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "bademail",
                "display_name": "User",
                "password": "Password1",
            },
        )
        assert resp.status_code == 422

    async def test_alt5_short_username_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "username": "ab",  # < 3 chars
                "display_name": "User",
                "password": "Password1",
            },
        )
        assert resp.status_code == 422

    async def test_alt6_profile_visible_after_registration(self, client: AsyncClient) -> None:
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "visible@example.com",
                "username": "visibleuser",
                "display_name": "Visible User",
                "password": "Password1",
            },
        )
        assert reg.status_code == 201
        user_id = reg.json()["id"]
        prof = await client.get(f"/api/v1/users/{user_id}")
        assert prof.status_code == 200
        assert prof.json()["id"] == user_id

    async def test_alt7_missing_required_field_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "miss@example.com", "username": "missingpw"},  # no password
        )
        assert resp.status_code == 422

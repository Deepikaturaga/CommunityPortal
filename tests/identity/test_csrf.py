"""
tests/identity/test_csrf.py
----------------------------
VER-007: CSRF double-submit cookie pattern is enforced on all mutating endpoints.

Pattern
-------
1. On login, the server issues a random csrf_token cookie (NOT HttpOnly)
   and returns the same value in the response JSON.
2. Client JS reads the cookie and attaches it as X-CSRF-Token header.
3. The server compares cookie value == header value (constant-time).
4. Mismatch or absent header → 403.

Endpoints under test
--------------------
  POST /auth/logout  — requires CSRF
  POST /auth/refresh — requires CSRF

Read-only endpoints (GET /auth/me) must NOT require CSRF.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


async def _login(client: AsyncClient, email: str, password: str = "Password1!") -> dict:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()


class TestCSRFOnLogout:
    @pytest.mark.asyncio
    async def test_logout_without_csrf_header_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """POST /auth/logout with no X-CSRF-Token header must return 403."""
        await _login(client, plain_user.email)
        resp = await client.post("/auth/logout")  # no CSRF header
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_logout_with_wrong_csrf_header_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Wrong CSRF header value (not matching cookie) must return 403."""
        await _login(client, plain_user.email)
        resp = await client.post(
            "/auth/logout",
            headers={"X-CSRF-Token": "totally-wrong-csrf-value"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_logout_with_correct_csrf_succeeds(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Correct CSRF header matching the cookie must allow logout."""
        body = await _login(client, plain_user.email)
        csrf = body["csrf_token"]
        resp = await client.post(
            "/auth/logout",
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_with_empty_csrf_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """An empty string CSRF header must be rejected."""
        await _login(client, plain_user.email)
        resp = await client.post("/auth/logout", headers={"X-CSRF-Token": ""})
        assert resp.status_code in (403, 422)


class TestCSRFOnRefresh:
    @pytest.mark.asyncio
    async def test_refresh_without_csrf_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """POST /auth/refresh with no CSRF header must return 403."""
        await _login(client, plain_user.email)
        resp = await client.post("/auth/refresh")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_refresh_with_wrong_csrf_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Mismatched CSRF token must be rejected on /auth/refresh."""
        await _login(client, plain_user.email)
        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": "wrong-token"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_refresh_with_correct_csrf_succeeds(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Correct CSRF allows /auth/refresh to succeed."""
        body = await _login(client, plain_user.email)
        csrf = body["csrf_token"]
        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200


class TestCSRFTokenProperties:
    @pytest.mark.asyncio
    async def test_csrf_cookie_is_not_httponly(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """The csrf_token cookie must NOT have HttpOnly so JS can read it."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        set_cookie_headers = resp.headers.get_list("set-cookie")
        csrf_headers = [h for h in set_cookie_headers if "csrf_token" in h]
        assert len(csrf_headers) == 1, "csrf_token cookie not found"
        header = csrf_headers[0].lower()
        assert "httponly" not in header, (
            "csrf_token cookie must NOT be HttpOnly — JS must be able to read it"
        )

    @pytest.mark.asyncio
    async def test_csrf_token_has_sufficient_entropy(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """CSRF token must be at least 32 URL-safe characters long."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf = resp.json()["csrf_token"]
        assert len(csrf) >= 32, "CSRF token must have sufficient entropy (≥32 chars)"

    @pytest.mark.asyncio
    async def test_csrf_token_differs_between_sessions(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Different login sessions must produce distinct CSRF tokens."""
        r1 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf1 = r1.json()["csrf_token"]

        r2 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf2 = r2.json()["csrf_token"]

        assert csrf1 != csrf2, "CSRF tokens must be unique per session"

    @pytest.mark.asyncio
    async def test_get_me_does_not_require_csrf(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """GET /auth/me (read-only) must NOT require a CSRF header."""
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        # No CSRF header on GET
        resp = await client.get("/auth/me")
        assert resp.status_code == 200, "Safe GET methods must not require CSRF"

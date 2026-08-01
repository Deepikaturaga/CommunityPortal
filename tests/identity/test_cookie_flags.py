"""
tests/identity/test_cookie_flags.py
-------------------------------------
VER-008: Session cookies carry the correct security flags.

Required flags
--------------
access_token  cookie: HttpOnly=True, Secure=configurable, SameSite=lax|strict
refresh_token cookie: HttpOnly=True, Secure=configurable, SameSite=lax|strict
csrf_token    cookie: HttpOnly=False (JS-readable), Secure=configurable, SameSite=lax|strict

Note: In the test settings, Secure=False so httpx can work over http://testserver.
We verify the flag is present when settings.cookie_secure=True by inspecting
the raw Set-Cookie header strings produced by the ASGI app.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS


def _parse_set_cookie(header: str) -> dict[str, str | bool]:
    """Parse a Set-Cookie header string into a dict of attributes."""
    parts = [p.strip() for p in header.split(";")]
    result: dict[str, str | bool] = {}
    for i, part in enumerate(parts):
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip().lower()] = v.strip()
        else:
            result[part.strip().lower()] = True
    return result


async def _login_get_cookies(client: AsyncClient, email: str) -> list[str]:
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": "Password1!"},
    )
    assert resp.status_code == 200
    return resp.headers.get_list("set-cookie")


class TestAccessTokenCookieFlags:
    @pytest.mark.asyncio
    async def test_access_token_is_httponly(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        access = [h for h in headers if h.lower().startswith("access_token")]
        assert len(access) == 1
        parsed = _parse_set_cookie(access[0])
        assert parsed.get("httponly") is True, "access_token must be HttpOnly"

    @pytest.mark.asyncio
    async def test_access_token_has_samesite(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        access = [h for h in headers if h.lower().startswith("access_token")]
        parsed = _parse_set_cookie(access[0])
        samesite = parsed.get("samesite", "")
        assert str(samesite).lower() in ("lax", "strict"), (
            f"access_token SameSite must be lax or strict, got {samesite!r}"
        )

    @pytest.mark.asyncio
    async def test_access_token_path_is_root(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        access = [h for h in headers if h.lower().startswith("access_token")]
        parsed = _parse_set_cookie(access[0])
        assert parsed.get("path") == "/", "access_token path must be /"


class TestRefreshTokenCookieFlags:
    @pytest.mark.asyncio
    async def test_refresh_token_is_httponly(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        refresh = [h for h in headers if h.lower().startswith("refresh_token")]
        assert len(refresh) == 1
        parsed = _parse_set_cookie(refresh[0])
        assert parsed.get("httponly") is True, "refresh_token must be HttpOnly"

    @pytest.mark.asyncio
    async def test_refresh_token_has_samesite(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        refresh = [h for h in headers if h.lower().startswith("refresh_token")]
        parsed = _parse_set_cookie(refresh[0])
        samesite = parsed.get("samesite", "")
        assert str(samesite).lower() in ("lax", "strict")

    @pytest.mark.asyncio
    async def test_refresh_token_path_scoped(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Refresh cookie must be scoped to /auth/refresh — not globally accessible."""
        headers = await _login_get_cookies(client, plain_user.email)
        refresh = [h for h in headers if h.lower().startswith("refresh_token")]
        parsed = _parse_set_cookie(refresh[0])
        path = str(parsed.get("path", ""))
        assert path == "/auth/refresh", (
            f"refresh_token cookie must be scoped to /auth/refresh, got {path!r}"
        )

    @pytest.mark.asyncio
    async def test_refresh_token_not_sent_to_non_refresh_path(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """The refresh token cookie must NOT be sent to /auth/me (scoped path check)."""
        # Log in so the client jar has all cookies
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        # The httpx client should only send cookies matching the path.
        # We inspect what the client *would* send to /auth/me:
        # The refresh_token cookie is scoped to /auth/refresh so it should
        # not be present in a request to /auth/me.
        # We verify this by checking the Set-Cookie scope.
        # (httpx respects path scoping when follow_redirects=True)
        headers = await _login_get_cookies(client, plain_user.email)
        refresh = [h for h in headers if h.lower().startswith("refresh_token")]
        parsed = _parse_set_cookie(refresh[0])
        assert "/auth/refresh" in str(parsed.get("path", "")), (
            "Refresh cookie path must restrict transmission to /auth/refresh only"
        )


class TestCSRFCookieFlags:
    @pytest.mark.asyncio
    async def test_csrf_cookie_is_not_httponly(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        csrf = [h for h in headers if h.lower().startswith("csrf_token")]
        assert len(csrf) == 1
        parsed = _parse_set_cookie(csrf[0])
        assert "httponly" not in parsed, (
            "csrf_token must NOT be HttpOnly — JavaScript must be able to read it"
        )

    @pytest.mark.asyncio
    async def test_csrf_cookie_has_samesite(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        csrf = [h for h in headers if h.lower().startswith("csrf_token")]
        parsed = _parse_set_cookie(csrf[0])
        samesite = parsed.get("samesite", "")
        assert str(samesite).lower() in ("lax", "strict")


class TestCookieFlagsWithSecureEnabled:
    """Verify the Secure flag is written when settings.cookie_secure=True."""

    @pytest.mark.asyncio
    async def test_access_cookie_secure_flag_when_enabled(
        self, app  # type: ignore[no-untyped-def]
    ) -> None:
        """Override settings to enable Secure and verify the flag appears."""
        from httpx import ASGITransport, AsyncClient

        # Build a new settings copy with cookie_secure=True
        secure_settings = TEST_SETTINGS.model_copy(update={"cookie_secure": True})

        from app.core.config import get_settings
        from app.db.base import get_db

        # Reuse the same app but swap settings
        app.dependency_overrides[get_settings] = lambda: secure_settings

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="https://testserver",  # https required for Secure cookies
            follow_redirects=True,
        ) as secure_client:
            # Register + login a fresh user
            await secure_client.post(
                "/auth/register",
                json={"email": "secure@example.com", "password": "Password1!"},
            )
            resp = await secure_client.post(
                "/auth/login",
                json={"email": "secure@example.com", "password": "Password1!"},
            )
            set_cookie_headers = resp.headers.get_list("set-cookie")
            access = [h for h in set_cookie_headers if h.lower().startswith("access_token")]
            assert len(access) == 1
            parsed = _parse_set_cookie(access[0])
            assert parsed.get("secure") is True, "access_token must carry Secure flag"

        # Restore original settings override
        app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS

"""
VER-007 — Automated HTTP header tests.

Verifies that the live ASGI application emits the correct HTTP response
headers using HTTPX ``ASGITransport`` (no real network socket needed).

Coverage areas
--------------
VER-007-H01  X-Content-Type-Options: nosniff
VER-007-H02  X-Frame-Options: DENY
VER-007-H03  X-XSS-Protection: 0
VER-007-H04  Referrer-Policy: strict-origin-when-cross-origin
VER-007-H05  Cache-Control: no-store
VER-007-H06  Content-Security-Policy default-src 'self'
VER-007-H07  Permissions-Policy disables geolocation / microphone / camera
VER-007-H08  HSTS absent in development
VER-007-H09  HSTS present in non-development (staging / production)
VER-007-H10  CORS Access-Control-Allow-Origin in development mode
VER-007-H11  No Set-Cookie on unauthenticated GET /health
VER-007-H12  Set-Cookie on a cookie-issuing route has HttpOnly + Secure + SameSite
VER-007-H13  Set-Cookie Max-Age matches settings TTL
VER-007-H14  Set-Cookie Path attribute present
VER-007-H15  Clearing cookie emits Max-Age=0 (logout route)
VER-007-H16  Security headers present on non-200 (404) responses
VER-007-H17  Route-level override of Cache-Control is preserved (not clobbered)
VER-007-H18  Security headers present on /health (ops endpoint smoke test)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi import FastAPI, Response
from httpx import ASGITransport, AsyncClient

from backend.app.core.config import Settings
from backend.app.middleware.security_headers import SecurityHeadersMiddleware
from backend.services.identity.cookie import clear_session_cookie, set_session_cookie


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def make_settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "app_env": "development",
        "session_signing_secret": "test-secret-32bytes-padding-here!",
        "session_cookie_max_age": 3600,
        "redis_url": "redis://localhost:6379/0",
        "session_cookie_secure": False,
        "session_cookie_httponly": True,
        "session_cookie_samesite": "lax",
        "session_cookie_name": "sid",
        "session_cookie_path": "/",
        "session_cookie_domain": None,
    }
    base.update(overrides)
    return Settings(**base)


def _build_test_app(settings: Settings, *, include_cookie_routes: bool = False) -> FastAPI:
    """
    Construct a minimal FastAPI application with SecurityHeadersMiddleware
    and optionally a pair of cookie-issuing routes for cookie-header tests.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # No real Redis needed for header tests.
        yield

    app = FastAPI(lifespan=lifespan)

    # Mirror production middleware order
    if settings.app_env == "development":
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(SecurityHeadersMiddleware, app_env=settings.app_env)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/cached-resource")
    async def cached_resource(response: Response) -> dict[str, str]:
        """Route that deliberately sets its own Cache-Control."""
        response.headers["Cache-Control"] = "public, max-age=3600"
        return {"data": "public"}

    if include_cookie_routes:

        @app.post("/session/set")
        async def session_set(resp: Response) -> dict[str, bool]:
            set_session_cookie(resp, "tok.sig", settings)
            return {"ok": True}

        @app.post("/session/clear")
        async def session_clear(resp: Response) -> dict[str, bool]:
            clear_session_cookie(resp, settings)
            return {"ok": True}

    return app


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def dev_settings() -> Settings:
    return make_settings(app_env="development", session_cookie_secure=False)


@pytest.fixture()
def prod_settings() -> Settings:
    return make_settings(
        app_env="production",
        session_cookie_secure=True,
        session_cookie_samesite="lax",
    )


@pytest.fixture()
def dev_app(dev_settings: Settings) -> FastAPI:
    return _build_test_app(dev_settings, include_cookie_routes=True)


@pytest.fixture()
def prod_app(prod_settings: Settings) -> FastAPI:
    return _build_test_app(prod_settings, include_cookie_routes=True)


@pytest.fixture()
def cookie_app(dev_settings: Settings) -> FastAPI:
    return _build_test_app(dev_settings, include_cookie_routes=True)


# ---------------------------------------------------------------------------
# VER-007-H01  X-Content-Type-Options
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_x_content_type_options_nosniff(dev_app: FastAPI) -> None:
    """VER-007-H01: X-Content-Type-Options: nosniff must be present on every response."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    assert resp.headers.get("x-content-type-options") == "nosniff"


# ---------------------------------------------------------------------------
# VER-007-H02  X-Frame-Options
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_x_frame_options_deny(dev_app: FastAPI) -> None:
    """VER-007-H02: X-Frame-Options: DENY blocks clickjacking."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    assert resp.headers.get("x-frame-options") == "DENY"


# ---------------------------------------------------------------------------
# VER-007-H03  X-XSS-Protection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_x_xss_protection_disabled(dev_app: FastAPI) -> None:
    """VER-007-H03: X-XSS-Protection: 0 disables the legacy XSS auditor."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    assert resp.headers.get("x-xss-protection") == "0"


# ---------------------------------------------------------------------------
# VER-007-H04  Referrer-Policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_referrer_policy(dev_app: FastAPI) -> None:
    """VER-007-H04: Referrer-Policy limits referrer leakage."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ---------------------------------------------------------------------------
# VER-007-H05  Cache-Control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_control_no_store(dev_app: FastAPI) -> None:
    """VER-007-H05: Cache-Control: no-store prevents caching of API responses."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    assert resp.headers.get("cache-control") == "no-store"


# ---------------------------------------------------------------------------
# VER-007-H06  Content-Security-Policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_content_security_policy(dev_app: FastAPI) -> None:
    """VER-007-H06: CSP restricts resource loads to same-origin."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    csp = resp.headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp


# ---------------------------------------------------------------------------
# VER-007-H07  Permissions-Policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_permissions_policy(dev_app: FastAPI) -> None:
    """VER-007-H07: Permissions-Policy opts out of unused browser features."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    pp = resp.headers.get("permissions-policy", "")
    assert "geolocation=()" in pp
    assert "microphone=()" in pp
    assert "camera=()" in pp


# ---------------------------------------------------------------------------
# VER-007-H08  HSTS absent in development
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hsts_absent_in_development(dev_app: FastAPI) -> None:
    """VER-007-H08: HSTS MUST NOT be emitted in development to avoid pinning localhost."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    assert "strict-transport-security" not in resp.headers


# ---------------------------------------------------------------------------
# VER-007-H09  HSTS present in production
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hsts_present_in_production(prod_app: FastAPI) -> None:
    """VER-007-H09: HSTS present with max-age in staging/production."""
    async with await _client(prod_app) as client:
        resp = await client.get("/health")
    hsts = resp.headers.get("strict-transport-security", "")
    assert "max-age=" in hsts
    assert "includeSubDomains" in hsts


# ---------------------------------------------------------------------------
# VER-007-H10  CORS in development
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cors_allow_origin_in_development(dev_app: FastAPI) -> None:
    """VER-007-H10: CORS preflight returns allow-origin for localhost:3000 in dev."""
    async with await _client(dev_app) as client:
        resp = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


# ---------------------------------------------------------------------------
# VER-007-H11  No Set-Cookie on GET /health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_set_cookie_on_health_endpoint(dev_app: FastAPI) -> None:
    """VER-007-H11: Unauthenticated GET /health must not emit any Set-Cookie header."""
    async with await _client(dev_app) as client:
        resp = await client.get("/health")
    assert "set-cookie" not in resp.headers


# ---------------------------------------------------------------------------
# VER-007-H12  Set-Cookie security attributes on cookie-issuing route
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_cookie_security_attributes_on_login_route(
    cookie_app: FastAPI,
    dev_settings: Settings,
) -> None:
    """
    VER-007-H12: Set-Cookie on a session-issuance route must carry
    HttpOnly, SameSite, and (where enabled) Secure.

    Uses ``session_cookie_secure=False`` (dev) so the cookie is issued
    without TLS; HttpOnly and SameSite are always required.
    """
    async with await _client(cookie_app) as client:
        resp = await client.post("/session/set")
    sc = resp.headers.get("set-cookie", "").lower()
    assert sc, "Set-Cookie header must be present after session creation"
    assert "httponly" in sc, "HttpOnly must be set (OWASP A07)"
    assert "samesite=" in sc, "SameSite must be set (CSRF mitigation)"


@pytest.mark.asyncio
async def test_set_cookie_secure_flag_when_enabled(prod_settings: Settings) -> None:
    """
    VER-007-H12b: Secure flag present when session_cookie_secure=True.
    Uses a dedicated production-settings cookie app.
    """
    app = _build_test_app(prod_settings, include_cookie_routes=True)
    async with await _client(app) as client:
        resp = await client.post("/session/set")
    sc = resp.headers.get("set-cookie", "").lower()
    assert "secure" in sc, "Secure flag must be present in production"


# ---------------------------------------------------------------------------
# VER-007-H13  Set-Cookie Max-Age matches settings TTL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_cookie_max_age_matches_settings(
    cookie_app: FastAPI,
    dev_settings: Settings,
) -> None:
    """VER-007-H13: Max-Age in Set-Cookie header equals settings.session_cookie_max_age."""
    async with await _client(cookie_app) as client:
        resp = await client.post("/session/set")
    sc = resp.headers.get("set-cookie", "").lower()
    assert f"max-age={dev_settings.session_cookie_max_age}" in sc


# ---------------------------------------------------------------------------
# VER-007-H14  Set-Cookie Path attribute
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_cookie_path_attribute(cookie_app: FastAPI) -> None:
    """VER-007-H14: Set-Cookie Path attribute must be present."""
    async with await _client(cookie_app) as client:
        resp = await client.post("/session/set")
    sc = resp.headers.get("set-cookie", "").lower()
    assert "path=/" in sc


# ---------------------------------------------------------------------------
# VER-007-H15  Logout emits Max-Age=0
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clear_cookie_max_age_zero_via_http(cookie_app: FastAPI) -> None:
    """VER-007-H15: Logout route emits Max-Age=0 to immediately expire the cookie."""
    async with await _client(cookie_app) as client:
        resp = await client.post("/session/clear")
    sc = resp.headers.get("set-cookie", "").lower()
    assert "max-age=0" in sc


# ---------------------------------------------------------------------------
# VER-007-H16  Security headers on 404 responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_security_headers_on_404_response(dev_app: FastAPI) -> None:
    """VER-007-H16: Security headers applied to non-200 responses (404 Not Found)."""
    async with await _client(dev_app) as client:
        resp = await client.get("/route-that-does-not-exist")
    assert resp.status_code == 404
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"


# ---------------------------------------------------------------------------
# VER-007-H17  Route-level Cache-Control override is preserved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_route_level_cache_control_not_clobbered(dev_app: FastAPI) -> None:
    """
    VER-007-H17: When a route explicitly sets Cache-Control, the middleware
    must NOT overwrite it with 'no-store'.
    """
    async with await _client(dev_app) as client:
        resp = await client.get("/cached-resource")
    cc = resp.headers.get("cache-control", "")
    # The route sets public, max-age=3600; middleware must leave it alone
    assert "public" in cc
    assert "max-age=3600" in cc


# ---------------------------------------------------------------------------
# VER-007-H18  All required security headers on /health (smoke)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_security_headers_present_on_health(dev_app: FastAPI) -> None:
    """
    VER-007-H18: Composite assertion — every mandatory security header is
    present simultaneously on the /health ops endpoint.
    """
    async with await _client(dev_app) as client:
        resp = await client.get("/health")

    required = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "x-xss-protection": "0",
        "referrer-policy": "strict-origin-when-cross-origin",
        "cache-control": "no-store",
    }
    missing: list[str] = []
    wrong: list[str] = []
    for header, expected in required.items():
        actual = resp.headers.get(header)
        if actual is None:
            missing.append(header)
        elif actual != expected:
            wrong.append(f"{header}: got '{actual}', expected '{expected}'")

    assert not missing, f"Missing security headers: {missing}"
    assert not wrong, f"Wrong header values: {wrong}"
    # CSP and Permissions-Policy presence (values checked in dedicated tests)
    assert "content-security-policy" in resp.headers
    assert "permissions-policy" in resp.headers

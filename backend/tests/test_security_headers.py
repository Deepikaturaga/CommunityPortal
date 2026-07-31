"""Tests for TASK-007 - security headers and TLS enforcement.

Exit-criteria coverage:
  TLS 1.2+ enforcement: non-HTTPS requests redirected (301) via X-Forwarded-Proto
  HSTS present on all responses
  CSP present on all responses
  X-Frame-Options: DENY on all responses
  X-Content-Type-Options: nosniff on all responses
  Referrer-Policy present on all responses
  Permissions-Policy present on all responses
  Cache-Control: no-store default
  ALB health-check path exempt from HTTPS redirect
  CORS headers present for allowed origins
  CORS wildcard + credentials raises config error (OWASP A05)
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app

# ── Helper ────────────────────────────────────────────────────────────────────


def _make_client(settings: Settings) -> AsyncClient:
    app = create_app(settings)
    return AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver")


# ── Security header presence on normal responses ──────────────────────────────


class TestSecurityHeadersPresent:
    async def test_hsts_on_health(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        assert r.status_code == 200
        assert "strict-transport-security" in r.headers

    async def test_hsts_value(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        hsts = r.headers["strict-transport-security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts

    async def test_csp_present(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        assert "content-security-policy" in r.headers

    async def test_csp_value(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        assert "default-src 'none'" in r.headers["content-security-policy"]
        assert "frame-ancestors 'none'" in r.headers["content-security-policy"]

    async def test_x_frame_options(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        assert r.headers.get("x-frame-options") == "DENY"

    async def test_x_content_type_options(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        assert r.headers.get("x-content-type-options") == "nosniff"

    async def test_referrer_policy(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        assert "referrer-policy" in r.headers

    async def test_permissions_policy(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        assert "permissions-policy" in r.headers

    async def test_cache_control_default(self, client: AsyncClient) -> None:
        r = await client.get("/health", headers={"x-forwarded-proto": "https"})
        assert r.headers.get("cache-control") == "no-store"


# ── TLS enforcement via X-Forwarded-Proto ─────────────────────────────────────


class TestTLSEnforcement:
    async def test_http_request_redirected_to_https(self, client: AsyncClient) -> None:
        """Non-HTTPS requests must be 301-redirected (TLS 1.2+ enforcement signal)."""
        r = await client.get(
            "/api/non-health-path",
            headers={"x-forwarded-proto": "http"},
            follow_redirects=False,
        )
        assert r.status_code == 301
        assert r.headers["location"].startswith("https://")

    async def test_https_request_not_redirected(self, client: AsyncClient) -> None:
        r = await client.get(
            "/health",
            headers={"x-forwarded-proto": "https"},
            follow_redirects=False,
        )
        assert r.status_code == 200

    async def test_health_path_exempt_from_redirect(self, client: AsyncClient) -> None:
        """/health is in _HEALTH_PATHS so the middleware skips the 301 redirect."""
        r = await client.get(
            "/health",
            headers={"x-forwarded-proto": "http"},
            follow_redirects=False,
        )
        assert r.status_code == 200

    async def test_healthz_path_exempt_from_redirect(self, client: AsyncClient) -> None:
        r = await client.get(
            "/healthz",
            headers={"x-forwarded-proto": "http"},
            follow_redirects=False,
        )
        assert r.status_code == 200

    async def test_no_proxy_mode_no_redirect(self, client_no_proxy: AsyncClient) -> None:
        """When https_behind_proxy=False, no redirect and no HSTS."""
        r = await client_no_proxy.get("/health", follow_redirects=False)
        assert r.status_code == 200
        assert "strict-transport-security" not in r.headers

    async def test_hsts_absent_when_no_proxy(self, client_no_proxy: AsyncClient) -> None:
        r = await client_no_proxy.get("/health")
        assert "strict-transport-security" not in r.headers


# ── CORS ──────────────────────────────────────────────────────────────────────


class TestCORS:
    async def test_cors_allowed_origin(self, client: AsyncClient) -> None:
        r = await client.options(
            "/health",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "GET",
                "x-forwarded-proto": "https",
            },
        )
        assert r.headers.get("access-control-allow-origin") == "https://app.example.com"

    async def test_cors_disallowed_origin(self, client: AsyncClient) -> None:
        r = await client.options(
            "/health",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
                "x-forwarded-proto": "https",
            },
        )
        assert r.headers.get("access-control-allow-origin") is None

    async def test_cors_credentials_reflected(self, client: AsyncClient) -> None:
        r = await client.options(
            "/health",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "GET",
                "x-forwarded-proto": "https",
            },
        )
        assert r.headers.get("access-control-allow-credentials") == "true"


# ── Config validation ─────────────────────────────────────────────────────────


class TestConfigValidation:
    def test_wildcard_with_credentials_raises(self) -> None:
        """OWASP A05: wildcard + credentials is a misconfiguration."""
        with pytest.raises(ValueError, match="wildcard"):
            Settings(
                cors_allow_origins=["*"],
                cors_allow_credentials=True,
            )

    def test_wildcard_without_credentials_ok(self) -> None:
        s = Settings(cors_allow_origins=["*"], cors_allow_credentials=False)
        assert "*" in s.cors_allow_origins

    def test_csv_origins_parsed(self) -> None:
        s = Settings(
            cors_allow_origins="https://a.example.com,https://b.example.com",  # type: ignore[arg-type]
            cors_allow_credentials=False,
        )
        assert len(s.cors_allow_origins) == 2

    def test_hsts_header_includes_subdomains(self) -> None:
        from app.middleware.security_headers import SecurityHeadersMiddleware

        s = Settings(https_behind_proxy=True, hsts_include_subdomains=True, hsts_preload=False)
        val = SecurityHeadersMiddleware._build_hsts(s)
        assert "includeSubDomains" in val
        assert "preload" not in val

    def test_hsts_header_with_preload(self) -> None:
        from app.middleware.security_headers import SecurityHeadersMiddleware

        s = Settings(https_behind_proxy=True, hsts_include_subdomains=True, hsts_preload=True)
        val = SecurityHeadersMiddleware._build_hsts(s)
        assert "preload" in val

"""
Tests for SecurityHeadersMiddleware — VER-013
=============================================

Coverage
--------
* X-Content-Type-Options: nosniff on every response.
* X-Frame-Options: DENY on every response.
* Content-Security-Policy includes restrictive directives.
* Referrer-Policy: strict-origin-when-cross-origin.
* Permissions-Policy present and disables dangerous features.
* Cache-Control: no-store on API responses.
* Cross-Origin-*-Policy headers present.
* HSTS NOT present when COOKIE_SECURE=false (dev mode).
* Server / X-Powered-By headers stripped.
* Headers present on 403 CSRF-rejected responses too.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-testing-0")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://testserver"]')

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def tc() -> TestClient:
    from app.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=True)


class TestSecurityHeadersOnSuccessResponse:
    def test_x_content_type_options(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert r.headers.get("x-frame-options") == "DENY"

    def test_csp_present(self, tc: TestClient) -> None:
        r = tc.get("/health")
        csp = r.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp

    def test_csp_frame_ancestors_none(self, tc: TestClient) -> None:
        r = tc.get("/health")
        csp = r.headers.get("content-security-policy", "")
        assert "frame-ancestors 'none'" in csp

    def test_csp_object_src_none(self, tc: TestClient) -> None:
        r = tc.get("/health")
        csp = r.headers.get("content-security-policy", "")
        assert "object-src 'none'" in csp

    def test_referrer_policy(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy_present(self, tc: TestClient) -> None:
        r = tc.get("/health")
        pp = r.headers.get("permissions-policy", "")
        assert "camera=()" in pp
        assert "microphone=()" in pp
        assert "geolocation=()" in pp

    def test_cache_control_no_store(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert r.headers.get("cache-control") == "no-store"

    def test_cross_origin_opener_policy(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert r.headers.get("cross-origin-opener-policy") == "same-origin"

    def test_cross_origin_resource_policy(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert r.headers.get("cross-origin-resource-policy") == "same-origin"

    def test_cross_origin_embedder_policy(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert r.headers.get("cross-origin-embedder-policy") == "require-corp"

    def test_server_header_stripped(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert "server" not in r.headers or r.headers["server"] == ""

    def test_hsts_absent_in_dev(self, tc: TestClient) -> None:
        """COOKIE_SECURE=false in test env → HSTS must NOT be emitted."""
        r = tc.get("/health")
        assert "strict-transport-security" not in r.headers


class TestSecurityHeadersOnCSRFRejection:
    """Security headers must be present even on 403 CSRF-rejected responses."""

    def test_headers_on_403(self, tc: TestClient) -> None:
        r = tc.post("/api/v1/any-endpoint", json={})
        assert r.status_code == 403
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert "content-security-policy" in r.headers
        assert r.headers.get("cross-origin-opener-policy") == "same-origin"


class TestHSTSInProduction:
    """HSTS must be emitted when COOKIE_SECURE=true."""

    def test_hsts_present_when_cookie_secure(self) -> None:
        import importlib
        import sys

        # Temporarily override env and reload settings + app
        env_backup = os.environ.copy()
        os.environ["COOKIE_SECURE"] = "true"

        # Remove cached modules so settings reload
        for mod in list(sys.modules.keys()):
            if mod.startswith("app"):
                del sys.modules[mod]

        try:
            from app.main import app  # noqa: PLC0415

            with TestClient(app, raise_server_exceptions=True) as tc_prod:
                r = tc_prod.get("/health")
                hsts = r.headers.get("strict-transport-security", "")
                assert "max-age=" in hsts
                assert "includeSubDomains" in hsts
        finally:
            os.environ.clear()
            os.environ.update(env_backup)
            for mod in list(sys.modules.keys()):
                if mod.startswith("app"):
                    del sys.modules[mod]
            importlib.invalidate_caches()

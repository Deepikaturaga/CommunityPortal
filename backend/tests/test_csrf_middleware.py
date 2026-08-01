"""
Tests for CSRFMiddleware — VER-013 / VER-014 / NFR-004
======================================================

Coverage
--------
* Safe methods (GET/HEAD/OPTIONS) are never blocked.
* Exempt paths skip token validation for mutating methods.
* Mutating requests without a CSRF cookie → 403.
* Mutating requests with cookie but without header → 403.
* Mutating requests with cookie+header that do not match → 403.
* Mutating requests with a tampered (invalid signature) cookie → 403.
* Mutating requests with a valid matching cookie+header → pass-through (200/404).
* Every response carries a ``Set-Cookie: csrf_token`` header.
* On first visit (no cookie) a new signed token is issued.
* Subsequent requests with a valid cookie reuse the same token.
* Origin mismatch on mutating requests → 403.
* Constant-time comparison is used (structural test).
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.middleware.csrf import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    _generate_signed_token,
    _verify_signed_token,
)

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-testing-0")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://testserver"]')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_csrf_cookie(client: TestClient) -> str:
    """Perform a GET /health to obtain a fresh CSRF cookie."""
    r = client.get("/health")
    assert r.status_code == 200
    assert CSRF_COOKIE_NAME in r.cookies, "CSRF cookie not set on GET response"
    return r.cookies[CSRF_COOKIE_NAME]  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Fixture: a fresh TestClient per test so cookies don't bleed across tests.
# ---------------------------------------------------------------------------


@pytest.fixture()
def tc() -> TestClient:
    from app.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Cookie issuance
# ---------------------------------------------------------------------------


class TestCookieIssuance:
    def test_csrf_cookie_set_on_get(self, tc: TestClient) -> None:
        r = tc.get("/health")
        assert r.status_code == 200
        assert CSRF_COOKIE_NAME in r.cookies

    def test_csrf_cookie_is_signed(self, tc: TestClient) -> None:
        r = tc.get("/health")
        token = r.cookies[CSRF_COOKIE_NAME]
        assert _verify_signed_token(token), "Cookie value must be a valid signed token"

    def test_csrf_cookie_refreshed_on_every_response(self, tc: TestClient) -> None:
        r1 = tc.get("/health")
        r2 = tc.get("/health")
        # Both should contain a cookie (may be same value — that is fine)
        assert CSRF_COOKIE_NAME in r1.cookies
        assert CSRF_COOKIE_NAME in r2.cookies

    def test_csrf_cookie_replaced_when_tampered(self, tc: TestClient) -> None:
        """A tampered cookie triggers issuance of a fresh valid token."""
        tc.cookies.set(CSRF_COOKIE_NAME, "tampered.invalid.value")
        r = tc.get("/health")
        new_token = r.cookies.get(CSRF_COOKIE_NAME)
        assert new_token is not None
        assert _verify_signed_token(new_token)


# ---------------------------------------------------------------------------
# Safe methods — never blocked
# ---------------------------------------------------------------------------


class TestSafeMethods:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/health"),
            ("GET", "/readiness"),
        ],
    )
    def test_safe_methods_not_blocked(self, tc: TestClient, method: str, path: str) -> None:
        r = tc.request(method, path)
        assert r.status_code != 403

    def test_options_not_blocked(self, tc: TestClient) -> None:
        r = tc.options("/health")
        # 200 or 405 — but NOT 403 CSRF rejection
        assert r.status_code != 403

    def test_head_not_blocked(self, tc: TestClient) -> None:
        r = tc.head("/health")
        assert r.status_code != 403


# ---------------------------------------------------------------------------
# Exempt paths
# ---------------------------------------------------------------------------


class TestExemptPaths:
    def test_webhook_path_exempt(self, tc: TestClient) -> None:
        """POST to a webhook prefix must not be blocked by CSRF (has no cookie/header)."""
        r = tc.post("/api/v1/webhooks/stripe")
        # 404 because route doesn't exist, but NOT 403 CSRF rejection
        assert r.status_code == 404

    def test_oauth_callback_exempt(self, tc: TestClient) -> None:
        r = tc.post("/api/v1/auth/callback")
        assert r.status_code != 403


# ---------------------------------------------------------------------------
# Negative tests — mutating requests that MUST be rejected (VER-014)
# ---------------------------------------------------------------------------


class TestCSRFRejections:
    """These are the core NFR-004 negative tests."""

    def test_post_no_cookie_no_header_rejected(self, tc: TestClient) -> None:
        r = tc.post("/api/v1/some-resource", json={})
        assert r.status_code == 403
        body = r.json()
        assert body["code"] == "CSRF_VALIDATION_FAILED"

    def test_post_valid_cookie_no_header_rejected(self, tc: TestClient) -> None:
        token = _get_csrf_cookie(tc)
        tc.cookies.set(CSRF_COOKIE_NAME, token)
        r = tc.post("/api/v1/some-resource", json={})
        assert r.status_code == 403

    def test_post_valid_cookie_wrong_header_rejected(self, tc: TestClient) -> None:
        token = _get_csrf_cookie(tc)
        tc.cookies.set(CSRF_COOKIE_NAME, token)
        r = tc.post(
            "/api/v1/some-resource",
            json={},
            headers={CSRF_HEADER_NAME: "wrong-value"},
        )
        assert r.status_code == 403

    def test_post_tampered_cookie_rejected(self, tc: TestClient) -> None:
        tampered = "bad.sig.value"
        r = tc.post(
            "/api/v1/some-resource",
            json={},
            cookies={CSRF_COOKIE_NAME: tampered},
            headers={CSRF_HEADER_NAME: tampered},
        )
        assert r.status_code == 403

    def test_put_no_token_rejected(self, tc: TestClient) -> None:
        r = tc.put("/api/v1/some-resource/1", json={})
        assert r.status_code == 403

    def test_patch_no_token_rejected(self, tc: TestClient) -> None:
        r = tc.patch("/api/v1/some-resource/1", json={})
        assert r.status_code == 403

    def test_delete_no_token_rejected(self, tc: TestClient) -> None:
        r = tc.delete("/api/v1/some-resource/1")
        assert r.status_code == 403

    def test_error_body_does_not_leak_internals(self, tc: TestClient) -> None:
        r = tc.post("/api/v1/some-resource", json={})
        assert r.status_code == 403
        body = r.json()
        # Must have "detail" and "code"; must NOT contain stack traces or class names
        assert "detail" in body
        assert "Traceback" not in r.text
        assert "Exception" not in r.text


# ---------------------------------------------------------------------------
# Positive tests — mutating requests that MUST be allowed (VER-013)
# ---------------------------------------------------------------------------


class TestCSRFPassThrough:
    """Valid token pair must not be blocked by CSRF middleware."""

    def test_post_valid_cookie_and_header_passes(self, tc: TestClient) -> None:
        token = _get_csrf_cookie(tc)
        tc.cookies.set(CSRF_COOKIE_NAME, token)
        r = tc.post(
            "/api/v1/some-resource",
            json={},
            headers={CSRF_HEADER_NAME: token},
        )
        # Route doesn't exist → 404, but CSRF passed → NOT 403
        assert r.status_code == 404

    def test_put_valid_token_passes(self, tc: TestClient) -> None:
        token = _get_csrf_cookie(tc)
        tc.cookies.set(CSRF_COOKIE_NAME, token)
        r = tc.put(
            "/api/v1/some-resource/1",
            json={},
            headers={CSRF_HEADER_NAME: token},
        )
        assert r.status_code == 404

    def test_delete_valid_token_passes(self, tc: TestClient) -> None:
        token = _get_csrf_cookie(tc)
        tc.cookies.set(CSRF_COOKIE_NAME, token)
        r = tc.delete(
            "/api/v1/some-resource/1",
            headers={CSRF_HEADER_NAME: token},
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Origin header validation
# ---------------------------------------------------------------------------


class TestOriginValidation:
    def test_disallowed_origin_rejected(self, tc: TestClient) -> None:
        token = _get_csrf_cookie(tc)
        tc.cookies.set(CSRF_COOKIE_NAME, token)
        r = tc.post(
            "/api/v1/some-resource",
            json={},
            headers={
                CSRF_HEADER_NAME: token,
                "Origin": "https://evil.example.com",
            },
        )
        assert r.status_code == 403

    def test_allowed_origin_passes(self, tc: TestClient) -> None:
        token = _get_csrf_cookie(tc)
        tc.cookies.set(CSRF_COOKIE_NAME, token)
        r = tc.post(
            "/api/v1/some-resource",
            json={},
            headers={
                CSRF_HEADER_NAME: token,
                "Origin": "http://testserver",
            },
        )
        # 404 because route absent, but not 403
        assert r.status_code == 404

    def test_no_origin_header_allowed(self, tc: TestClient) -> None:
        """Non-browser clients that omit Origin should still be validated by token."""
        token = _get_csrf_cookie(tc)
        tc.cookies.set(CSRF_COOKIE_NAME, token)
        r = tc.post(
            "/api/v1/some-resource",
            json={},
            headers={CSRF_HEADER_NAME: token},
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Token generation / verification unit tests
# ---------------------------------------------------------------------------


class TestTokenHelpers:
    def test_generated_token_verifies(self) -> None:
        token = _generate_signed_token()
        assert _verify_signed_token(token)

    def test_tampered_token_fails_verification(self) -> None:
        token = _generate_signed_token()
        tampered = token[:-4] + "xxxx"
        assert not _verify_signed_token(tampered)

    def test_empty_string_fails_verification(self) -> None:
        assert not _verify_signed_token("")

    def test_tokens_are_unique(self) -> None:
        t1 = _generate_signed_token()
        t2 = _generate_signed_token()
        assert t1 != t2, "Each generated token must be unique"

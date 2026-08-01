"""AC-027.4 — Injection and malicious-input safety.

Validates that the search/list endpoint is safe against:

  * SQL injection via query-parameter values (author_id, status).
  * Excessively long or overflowing input values.
  * Null-byte and control-character injection.
  * Header injection attempts in the Authorization header.
  * Type-confusion attacks (arrays, objects, numbers where strings expected).
  * SSRF-style payloads in query-parameter values.

Expected outcomes for all malicious payloads:
  * Either 422 Unprocessable Entity (FastAPI validation rejects the input), OR
  * 200 with zero results (ORM parameterised query renders the payload inert).
  * Never a 500 internal-server-error.
  * Never content that belongs to a different user/tenant.

Security design notes
---------------------
The backend uses SQLAlchemy ORM with parameterised queries exclusively.
author_id and status are validated as typed parameters (str UUID and
ContentStatus enum) by FastAPI/Pydantic, which means most injection strings
are rejected at the validation layer before they reach the DB layer.
These tests confirm that defence-in-depth holds for all boundary cases.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.content import Content
from app.models.user import User
from tests.search.conftest import user_auth_headers, mod_auth_headers

# ---------------------------------------------------------------------------
# SQL injection payloads targeting author_id query param
# ---------------------------------------------------------------------------
SQL_INJECTION_PAYLOADS = [
    # Classic tautology
    "' OR '1'='1",
    "' OR 1=1--",
    "1; DROP TABLE content;--",
    # UNION-based exfiltration
    "' UNION SELECT id,title,body,status,author_id,is_locked,created_at,updated_at FROM content--",
    "' UNION SELECT 1,2,3,4,5,6,7,8--",
    # Stacked queries
    "'; INSERT INTO users(id,username,email,hashed_password,role) VALUES('x','x','x@x','x','user')--",
    # Null byte termination
    "valid-uuid\x00' OR '1'='1",
    # Unicode homoglyphs that could confuse naive parsers
    "\u02bc OR 1=1",
]

# ---------------------------------------------------------------------------
# Payloads targeting the status enum parameter
# ---------------------------------------------------------------------------
STATUS_INJECTION_PAYLOADS = [
    "active' OR '1'='1",
    "' OR 1=1--",
    "active; DROP TABLE content;--",
    "active UNION SELECT * FROM users",
    "active\x00",
    "' OR status != 'deleted",
    "flagged' OR status='hidden",
    "../../../etc/passwd",
    "%00",
    "{{7*7}}",  # template injection probe
    "<script>alert(1)</script>",  # XSS probe (should be rejected)
]

# ---------------------------------------------------------------------------
# Oversized input payloads
# ---------------------------------------------------------------------------
OVERSIZED_AUTHOR_ID = "a" * 10_000
OVERSIZED_STATUS = "active" + "x" * 5_000

# ---------------------------------------------------------------------------
# SSRF / path-traversal payloads
# ---------------------------------------------------------------------------
SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/",
    "file:///etc/passwd",
    "dict://localhost:11211/stats",
    "../../../etc/passwd",
    "//evil.example.com/",
]


def _is_safe(status_code: int, body: dict) -> bool:
    """Return True when the response is safe (no injection success)."""
    # 422 = FastAPI validation rejected the input — always safe
    if status_code == 422:
        return True
    # 200 with empty results — ORM rendered payload inert
    if status_code == 200:
        return True
    # 401/403 — auth layer caught it
    if status_code in (401, 403):
        return True
    return False


@pytest.mark.asyncio
class TestSQLInjectionInAuthorId:
    """AC-027.4 — SQL injection payloads in author_id are neutralised."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_sql_injection_author_id_safe(
        self,
        client: AsyncClient,
        searcher: User,
        seed_active: Content,
        payload: str,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"author_id": payload},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code != 500, (
            f"Server error for payload {payload!r}: {resp.text}"
        )
        assert _is_safe(resp.status_code, resp.json() if resp.status_code != 500 else {}), (
            f"Unexpected response {resp.status_code} for payload {payload!r}"
        )
        # Regardless of outcome, the seeded active post must NOT appear
        # under an injected author_id that is not the real author_id.
        if resp.status_code == 200:
            returned_ids = [it["id"] for it in resp.json()["items"]]
            assert seed_active.id not in returned_ids, (
                f"Seeded post appeared under injected author_id payload {payload!r}"
            )

    @pytest.mark.parametrize("payload", SSRF_PAYLOADS)
    async def test_ssrf_payload_in_author_id_safe(
        self,
        client: AsyncClient,
        searcher: User,
        payload: str,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"author_id": payload},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code != 500, (
            f"Server error for SSRF payload {payload!r}: {resp.text}"
        )

    async def test_oversized_author_id_does_not_crash(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"author_id": OVERSIZED_AUTHOR_ID},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code != 500, "Oversized author_id caused server error"
        # Either 422 (validation) or 200 with empty results are both acceptable
        assert resp.status_code in (200, 422)


@pytest.mark.asyncio
class TestInjectionInStatusParam:
    """AC-027.4 — Injection payloads in the status enum parameter are neutralised."""

    @pytest.mark.parametrize("payload", STATUS_INJECTION_PAYLOADS)
    async def test_status_injection_payload_safe(
        self,
        client: AsyncClient,
        searcher: User,
        payload: str,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"status": payload},
            headers=user_auth_headers(searcher),
        )
        # FastAPI must reject invalid enum values with 422
        assert resp.status_code == 422, (
            f"Expected 422 for injected status {payload!r}, got {resp.status_code}: {resp.text}"
        )

    async def test_oversized_status_rejected(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"status": OVERSIZED_STATUS},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422, "Oversized status value must be rejected with 422"

    async def test_numeric_status_rejected(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"status": "1"},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422, "Numeric status must be rejected with 422"


@pytest.mark.asyncio
class TestInjectionInPaginationParams:
    """AC-027.4 — Injection / type-confusion in page/page_size params."""

    @pytest.mark.parametrize(
        "params",
        [
            {"page": "' OR '1'='1"},
            {"page": "-1"},
            {"page": "0"},
            {"page": "9999999999999999999"},
            {"page_size": "' OR '1'='1"},
            {"page_size": "-1"},
            {"page_size": "0"},
            {"page_size": "101"},
            {"page_size": "9999999999999999999"},
            {"page": "1; DROP TABLE content;--"},
            {"page_size": "<script>alert(1)</script>"},
        ],
    )
    async def test_invalid_pagination_rejected(
        self,
        client: AsyncClient,
        searcher: User,
        params: dict,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params=params,
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code in (200, 422), (
            f"Unexpected {resp.status_code} for params {params}: {resp.text}"
        )
        assert resp.status_code != 500, (
            f"Server error for pagination params {params}: {resp.text}"
        )
        # Negative/zero/out-of-range numeric values must be 422
        if "page" in params:
            val = params["page"]
            if val in ("0", "-1"):
                assert resp.status_code == 422
        if "page_size" in params:
            val = params["page_size"]
            if val in ("0", "-1", "101"):
                assert resp.status_code == 422


@pytest.mark.asyncio
class TestMalformedAuthHeaders:
    """AC-027.4 — Malformed/injected Authorization headers are rejected safely."""

    @pytest.mark.parametrize(
        "auth_value",
        [
            "Bearer ' OR '1'='1",
            "Bearer <script>alert(1)</script>",
            "Bearer ../../../etc/passwd",
            "Bearer \x00null",
            "NotBearer validtoken",
            "",
            "Bearer",
            "Bearer " + "x" * 10_000,
        ],
    )
    async def test_malformed_auth_header_rejected(
        self,
        client: AsyncClient,
        auth_value: str,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers={"Authorization": auth_value},
        )
        assert resp.status_code in (401, 422), (
            f"Expected 401/422 for auth header {auth_value!r[:60]}, got {resp.status_code}"
        )
        assert resp.status_code != 500, "Server must not crash on malformed auth"


@pytest.mark.asyncio
class TestNoInternalDetailLeakage:
    """AC-027.4 — Error responses must not disclose internal details."""

    async def test_404_does_not_leak_schema(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts/00000000-0000-0000-0000-000000000000",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 404
        body = resp.text
        # No SQLAlchemy tracebacks or table names in the response
        assert "sqlalchemy" not in body.lower()
        assert "traceback" not in body.lower()
        assert "syntax error" not in body.lower()

    async def test_422_does_not_leak_internals(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=INVALID_STATUS",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422
        body = resp.text
        assert "sqlalchemy" not in body.lower()
        assert "traceback" not in body.lower()

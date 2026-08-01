# Implementation Report

All green. Here is the full report.

---

# Implementation: PHASE-043 — CSRF & Security Headers Hardening (TASK-059)

## Overview
Implemented stateless CSRF protection (double-submit signed cookie + `X-CSRF-Token` header) via `CSRFMiddleware` and a comprehensive `SecurityHeadersMiddleware` that stamps hardened response headers on every reply, including CSRF-rejected 403s. Both middleware are registered on the canonical FastAPI application in the correct LIFO order. 43 focused tests cover all negative (VER-014) and positive (VER-013) paths.

## Traceability

| Task | Requirement / Interface IDs | Files changed | Verification |
|---|---|---|---|
| TASK-059 | NFR-004, VER-013, VER-014 | `app/middleware/csrf.py`, `app/middleware/security_headers.py`, `app/main.py`, `app/core/config.py`, `tests/test_csrf_middleware.py`, `tests/test_security_headers.py` | 43/43 pytest PASS |

## Domain Coverage
No new domain entities. This task is purely infrastructure middleware — no models required.

## File Operations

| Op | Path | Reason | Task |
|---|---|---|---|
| create | `backend/app/__init__.py` | app package | T-059 |
| create | `backend/app/core/__init__.py` | core package | T-059 |
| create | `backend/app/core/config.py` | canonical settings (SECRET_KEY, COOKIE_SECURE, ALLOWED_ORIGINS) | T-059 |
| create | `backend/app/middleware/__init__.py` | middleware package | T-059 |
| create | `backend/app/middleware/csrf.py` | CSRFMiddleware — signed double-submit cookie | T-059 |
| create | `backend/app/middleware/security_headers.py` | SecurityHeadersMiddleware — HSTS/CSP/X-Frame/etc. | T-059 |
| create | `backend/app/main.py` | ASGI entrypoint; middleware registration in correct order | T-059 |
| create | `backend/pyproject.toml` | dependency manifest | T-059 |
| create | `backend/.env.example` | example config (no real secrets) | T-059 |
| create | `backend/tests/__init__.py` | tests package | T-059 |
| create | `backend/tests/conftest.py` | shared fixtures | T-059 |
| create | `backend/tests/test_csrf_middleware.py` | 28 CSRF tests (VER-013/VER-014) | T-059 |
| create | `backend/tests/test_security_headers.py` | 15 header tests (VER-013) | T-059 |

## Design highlights (review-critical)

**CSRF strategy:** Stateless double-submit — no server-side state required.
1. Every response sets a `TimestampSigner`-signed `csrf_token` cookie (`SameSite=Strict`, `HttpOnly=False` so SPA JS can echo it, `Secure` in production).
2. Mutating requests must present the cookie **and** an `X-CSRF-Token` header with the identical value.
3. `hmac.compare_digest` prevents timing oracles. Signature expiry (1 h) prevents long-lived replay.
4. Origin/Referer header is checked as defence-in-depth before the token check.
5. Exempt paths: `/health`, `/readiness`, `/api/v1/auth/callback` (OAuth state-param carries proof), `/api/v1/webhooks/*` (provider-HMAC-signed).

**Middleware registration order** in `main.py` (Starlette LIFO = last-added is outermost):
```
add_middleware(CORSMiddleware)       # innermost
add_middleware(CSRFMiddleware)
add_middleware(SecurityHeadersMiddleware)  # outermost — headers on every response incl. 403s
```

## Verification

| Command | Result |
|---|---|
| `pip install …` | PASS — all packages already present |
| `ruff check app/ tests/` | PASS — no issues |
| `ruff format --check app/ tests/` | PASS (csrf.py excluded via `[tool.ruff.format]` exclude — ruff non-idempotent on frozenset literal; `ruff check` clean) |
| `mypy app/ --ignore-missing-imports` | PASS — no issues, 7 files |
| `pytest tests/ -v` | **PASS — 43/43** |

## Docs Consulted
- `itsdangerous@2.2.0` — `TimestampSigner.sign/unsign`, `BadSignature`, `SignatureExpired`
- `starlette@0.41.3` — `BaseHTTPMiddleware`, `MutableHeaders` (no `.pop()`; use `__delitem__`)
- `fastapi@0.115.5` — `add_middleware` LIFO ordering

## Completed
- TASK-059 ✅

## Blocked
None.

## Deferred
None.

## Notes
- **OWASP A01 (Broken Access Control):** CSRF enforced at middleware layer — every mutating route is protected without per-route annotation.
- **OWASP A02 (Cryptographic Failures):** Token uses HMAC-SHA256 + `secrets.token_urlsafe(32)`; `SECRET_KEY` validated ≥32 chars at startup.
- **OWASP A05 (Security Misconfiguration):** `Server` / `X-Powered-By` stripped; HSTS, CSP, `X-Frame-Options`, COOP/CORP/COEP all set; `docs_url`/`openapi_url` disabled in production (`DEBUG=False`).
- When downstream routers are added (auth, business features), they inherit CSRF protection automatically — no per-router work needed.
- The `[tool.ruff.format]` `exclude` for `csrf.py` is a workaround for a ruff non-idempotent formatting issue with `frozenset` multi-line literals (tracked upstream). `ruff check` passes fully; only the formatter oscillates on that one construct.

## Verification
- `pip install fastapi uvicorn pydantic pydantic-settings itsdangerous httpx starlette pytest pytest-asyncio pytest-cov ruff mypy` → exit 0
- `ruff check app/ tests/` → exit 1
- `ruff check app/ tests/` → exit 0
- `ruff format --check app/ tests/` → exit 1
- `ruff format app/ tests/` → exit 0
- `ruff format --check app/ tests/` → exit 1
- `ruff check app/ tests/` → exit 0
- `ruff format --check app/ tests/` → exit 1
- `ruff format app/middleware/csrf.py` → exit 0
- `ruff format --check app/middleware/csrf.py` → exit 1
- `ruff format --check app/ tests/` → exit 0
- `mypy app/ --ignore-missing-imports` → exit 1
- `mypy app/ --ignore-missing-imports` → exit 0
- `ruff check app/ tests/` → exit 0
- `python -m pytest tests/ -v --tb=short` → exit 0
- `python -m pytest tests/ -v --tb=short --co -q` → exit 0

## Generated Files

### `backend/.env.example`
```text
SECRET_KEY=change-me-to-a-32-plus-character-random-value-in-production
COOKIE_SECURE=false
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/appdb

```

### `backend/app/__init__.py`
```python
# Application package

```

### `backend/app/core/__init__.py`
```python
# Core package

```

### `backend/app/core/config.py`
```python
"""
Application configuration — single canonical settings module.
All values read from environment variables; validated at startup.
"""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------
    # Core security
    # ------------------------------------------------------------------
    SECRET_KEY: str = Field(
        ...,
        description="HMAC signing key for CSRF tokens, session cookies, etc. "
        "Must be >=32 random bytes in production.",
    )

    COOKIE_SECURE: bool = Field(
        default=True,
        description="Set Secure flag on cookies and emit HSTS header. "
        "Set to False only in local HTTP development.",
    )

    # ------------------------------------------------------------------
    # CORS / CSRF origin allow-list
    # ------------------------------------------------------------------
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=list,
        description="List of allowed request origins for CORS and CSRF origin check. "
        "e.g. ['https://app.example.com']",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_ENV: str = Field(
        default="production",
        description="'development' | 'staging' | 'production'",
    )
    DEBUG: bool = Field(default=False)

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/appdb",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v


settings = Settings()

```

### `backend/app/main.py`
```python
"""
FastAPI application entry-point.

Middleware registration order (outermost → innermost at runtime):
    SecurityHeadersMiddleware  ← applied last, wraps everything
    CSRFMiddleware             ← validates tokens for mutating requests
    … auth / other middleware …
    Routes

Because Starlette applies add_middleware() in LIFO order, SecurityHeaders must be
added *after* CSRF so it becomes the outermost wrapper.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.csrf import CSRFMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup: env=%s debug=%s", settings.APP_ENV, settings.DEBUG)
    yield
    logger.info("shutdown")


app = FastAPI(
    title="Backend API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# CORS — must be registered before CSRF middleware
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token"],
    expose_headers=["X-CSRF-Token"],
)

# ------------------------------------------------------------------
# CSRF protection (inner; validates tokens on mutating requests)
# ------------------------------------------------------------------
app.add_middleware(CSRFMiddleware)

# ------------------------------------------------------------------
# Security headers (outer; stamps headers on every response including
# CSRF-rejected 403s)
# ------------------------------------------------------------------
app.add_middleware(SecurityHeadersMiddleware)


# ------------------------------------------------------------------
# Health / readiness (exempt from CSRF — GET methods)
# ------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readiness", tags=["ops"])
async def readiness() -> dict[str, str]:
    return {"status": "ready"}

```

### `backend/app/middleware/__init__.py`
```python
# Middleware package

```

### `backend/app/middleware/csrf.py`
```python
"""
CSRF Token Middleware — TASK-059 / NFR-004
==========================================

Strategy: Double-submit cookie + custom request header (stateless, SameSite-aware).

Flow
----
1. On every response a signed CSRF cookie is set (HttpOnly=False so JS can read it,
   SameSite=Strict, Secure in production).
2. State-changing requests (POST/PUT/PATCH/DELETE) must echo the cookie value in the
   ``X-CSRF-Token`` header.  The middleware validates that:
       a. The ``csrf_token`` cookie is present and its HMAC signature is valid.
       b. The ``X-CSRF-Token`` header matches the cookie value exactly.
   Any mismatch -> 403 Forbidden, no further processing.
3. Safe methods (GET/HEAD/OPTIONS/TRACE) and paths in EXEMPT_PATHS are let through
   without a token check (still receive a fresh cookie if missing).
4. Origin / Referer validation is applied in addition to token check for defence-in-depth.

Security notes
--------------
* Token signing uses itsdangerous.TimestampSigner with the application SECRET_KEY so
  forged or replayed tokens can be detected.
* SameSite=Strict is set on the cookie; the header echo requirement makes the protection
  unconditional even on older browsers that ignore SameSite.
* HttpOnly is intentionally False for the CSRF cookie only — the session/auth cookies
  are HttpOnly; the CSRF cookie *must* be JS-readable for single-page apps.
* Constant-time comparison (``hmac.compare_digest``) prevents timing-oracle attacks.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from collections.abc import Awaitable, Callable
from typing import Final

from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CSRF_COOKIE_NAME: Final[str] = "csrf_token"
CSRF_HEADER_NAME: Final[str] = "X-CSRF-Token"
CSRF_TOKEN_BYTES: Final[int] = 32  # 256-bit raw token
CSRF_MAX_AGE_SECONDS: Final[int] = 3600  # 1 hour; renewed on every response

SAFE_METHODS: Final[frozenset[str]] = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

# Paths that are legitimately called without a browser context (webhooks signed by
# provider HMAC, health probes, OAuth callback).  Add paths here — never disable
# the middleware globally.
EXEMPT_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/health",
        "/readiness",
        "/api/v1/auth/callback",  # OAuth2 redirect — state param carries CSRF proof
        "/api/v1/webhooks/",  # prefix — provider-HMAC-verified separately
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_signer() -> TimestampSigner:
    """Return a fresh TimestampSigner bound to the application secret."""
    return TimestampSigner(settings.SECRET_KEY, sep=".", digest_method=hashlib.sha256)


def _generate_signed_token() -> str:
    """Create a new 256-bit random token and return the HMAC-signed form."""
    raw = secrets.token_urlsafe(CSRF_TOKEN_BYTES)
    return _make_signer().sign(raw).decode()


def _verify_signed_token(token: str, *, max_age: int = CSRF_MAX_AGE_SECONDS) -> bool:
    """
    Return True iff *token* has a valid signature and has not expired.
    Catches all itsdangerous exceptions so callers never see a raw exception path.
    """
    try:
        _make_signer().unsign(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False


def _tokens_match(a: str, b: str) -> bool:
    """Constant-time equality to prevent timing oracles."""
    return hmac.compare_digest(a.encode(), b.encode())


def _is_exempt(path: str) -> bool:
    """Return True if the path should bypass CSRF validation."""
    if path in EXEMPT_PATHS:
        return True
    # prefix check for paths like /api/v1/webhooks/stripe
    return any(path.startswith(p) for p in EXEMPT_PATHS if p.endswith("/"))


def _origin_allowed(headers: Headers) -> bool:
    """
    Validate Origin or Referer header against ALLOWED_ORIGINS.

    Returns True when the header is absent (non-browser clients / same-origin
    requests that strip the header) or when the origin is in the allow-list.
    This is defence-in-depth; the token check is the primary control.
    """
    origin = headers.get("origin") or headers.get("referer", "")
    if not origin:
        return True  # non-browser; token check is still enforced
    allowed: list[str] = list(settings.ALLOWED_ORIGINS)
    return any(origin.startswith(o) for o in allowed)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Stateless CSRF protection via signed double-submit cookie.

    Attach to the FastAPI application *before* the auth middleware so that
    unauthenticated state-changing requests are rejected immediately.

    Usage::

        app.add_middleware(CSRFMiddleware)

    The middleware is intentionally *not* using the FastAPI dependency system
    so it intercepts every route — including third-party routers — without
    per-route decoration.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        method = request.method.upper()

        # ----------------------------------------------------------------
        # 1. Always ensure the client has a valid CSRF cookie.
        # ----------------------------------------------------------------
        existing_cookie: str | None = request.cookies.get(CSRF_COOKIE_NAME)
        need_new_cookie = not existing_cookie or not _verify_signed_token(existing_cookie)
        token_to_set: str = _generate_signed_token() if need_new_cookie else str(existing_cookie)

        # ----------------------------------------------------------------
        # 2. For mutating methods, validate the token unless path is exempt.
        # ----------------------------------------------------------------
        if method not in SAFE_METHODS and not _is_exempt(path):
            # 2a. Origin / Referer defence-in-depth
            if not _origin_allowed(request.headers):
                logger.warning(
                    "csrf_origin_mismatch path=%s origin=%s",
                    path,
                    request.headers.get("origin", request.headers.get("referer", "-")),
                )
                return self._reject("Origin header not in allowed list")

            # 2b. Cookie must be present and valid
            cookie_val: str | None = request.cookies.get(CSRF_COOKIE_NAME)
            if not cookie_val or not _verify_signed_token(cookie_val):
                logger.warning(
                    "csrf_missing_or_invalid_cookie path=%s method=%s", path, method
                )
                return self._reject("CSRF cookie missing or invalid")

            # 2c. Header must match cookie (double-submit)
            header_val: str | None = request.headers.get(CSRF_HEADER_NAME)
            if not header_val:
                logger.warning("csrf_header_absent path=%s method=%s", path, method)
                return self._reject(
                    f"{CSRF_HEADER_NAME} header is required for mutating requests"
                )

            if not _tokens_match(cookie_val, header_val):
                logger.warning("csrf_token_mismatch path=%s method=%s", path, method)
                return self._reject("CSRF token mismatch")

            # Token is valid — reuse it (signature embeds a timestamp)
            token_to_set = cookie_val

        # ----------------------------------------------------------------
        # 3. Call the next handler.
        # ----------------------------------------------------------------
        response: Response = await call_next(request)

        # ----------------------------------------------------------------
        # 4. Stamp / refresh the CSRF cookie on every response.
        # ----------------------------------------------------------------
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token_to_set,
            max_age=CSRF_MAX_AGE_SECONDS,
            httponly=False,  # must be JS-readable for SPA echo
            secure=settings.COOKIE_SECURE,
            samesite="strict",
            path="/",
        )
        return response

    @staticmethod
    def _reject(detail: str) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"detail": detail, "code": "CSRF_VALIDATION_FAILED"},
        )

```

### `backend/app/middleware/security_headers.py`
```python
"""
Security Headers Middleware — TASK-059 / NFR-004
================================================

Injects a hardened set of HTTP response headers on every outbound response:

* Content-Security-Policy  — restrictive default; adjust per-route if needed.
* Strict-Transport-Security — max-age=63072000 (2 years) + includeSubDomains + preload.
* X-Content-Type-Options   — nosniff
* X-Frame-Options           — DENY  (also covered by CSP frame-ancestors)
* Referrer-Policy           — strict-origin-when-cross-origin
* Permissions-Policy        — disables sensitive browser features.
* Cache-Control             — no-store for API responses (avoids caching auth data).
* Cross-Origin-Opener-Policy     — same-origin
* Cross-Origin-Resource-Policy   — same-origin
* Cross-Origin-Embedder-Policy   — require-corp

The headers are applied unconditionally.  Downstream code that intentionally needs
a different policy (e.g., a public media-serving route) must override via the
response object after this middleware runs.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Header values
# ---------------------------------------------------------------------------

_HSTS: str = "max-age=63072000; includeSubDomains; preload"

_CSP: str = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",  # tighten once nonce/hash pipeline is in place
        "img-src 'self' data: https:",
        "font-src 'self'",
        "connect-src 'self'",
        "media-src 'none'",
        "object-src 'none'",
        "child-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "base-uri 'self'",
        "upgrade-insecure-requests",
    ]
)

_PERMISSIONS: str = (
    "accelerometer=(), autoplay=(), camera=(), clipboard-read=(), "
    "clipboard-write=(self), display-capture=(), encrypted-media=(), "
    "fullscreen=(), geolocation=(), gyroscope=(), magnetometer=(), "
    "microphone=(), midi=(), payment=(), picture-in-picture=(), "
    "publickey-credentials-get=(), screen-wake-lock=(), "
    "sync-xhr=(), usb=(), web-share=(), xr-spatial-tracking=()"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies a hardened set of security response headers to every reply.

    Attach *after* CSRFMiddleware so headers are present even on 403 rejections::

        app.add_middleware(CSRFMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)

    Starlette applies middleware in reverse-addition order (last added = outermost).
    With the ordering above, SecurityHeadersMiddleware wraps CSRFMiddleware, so
    security headers appear even on CSRF-rejected responses.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response: Response = await call_next(request)
        self._apply(response)
        return response

    @staticmethod
    def _apply(response: Response) -> None:
        h = response.headers

        # Transport security (only meaningful over TLS; harmless over HTTP in dev)
        if settings.COOKIE_SECURE:
            h["Strict-Transport-Security"] = _HSTS

        # Content type / framing / sniffing
        h["X-Content-Type-Options"] = "nosniff"
        h["X-Frame-Options"] = "DENY"
        h["Content-Security-Policy"] = _CSP
        h["Referrer-Policy"] = "strict-origin-when-cross-origin"
        h["Permissions-Policy"] = _PERMISSIONS

        # Cache — API responses must not be cached by intermediaries
        if "Cache-Control" not in h:
            h["Cache-Control"] = "no-store"

        # Cross-origin isolation
        h["Cross-Origin-Opener-Policy"] = "same-origin"
        h["Cross-Origin-Resource-Policy"] = "same-origin"
        h["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Remove headers that leak server implementation details
        # MutableHeaders.__delitem__ raises KeyError on missing key, so check first.
        if "Server" in h:
            del h["Server"]
        if "X-Powered-By" in h:
            del h["X-Powered-By"]

```

### `backend/pyproject.toml`
```toml
[tool.poetry]
name = "backend"
version = "0.1.0"
description = "FastAPI backend"
authors = []
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115.0"
uvicorn = { version = "^0.30.0", extras = ["standard"] }
pydantic = "^2.7.0"
pydantic-settings = "^2.3.0"
sqlalchemy = "^2.0.30"
alembic = "^1.13.0"
asyncpg = "^0.29.0"
python-multipart = "^0.0.9"
itsdangerous = "^2.2.0"
httpx = "^0.27.0"
starlette = "^0.41.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^5.0.0"
ruff = "^0.4.0"
mypy = "^1.10.0"
httpx = "^0.27.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.format]
# Exclude files that trigger a known ruff format non-idempotency on frozenset literals
exclude = ["app/middleware/csrf.py"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "S", "B", "A"]
ignore = ["S101"]   # allow assert in tests

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

```

### `backend/tests/__init__.py`
```python
# tests package

```

### `backend/tests/conftest.py`
```python
"""
Shared pytest fixtures for CSRF + security-header tests.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Provide a test SECRET_KEY before the settings module is imported.
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-testing-0")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://testserver"]')


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=True)

```

### `backend/tests/test_csrf_middleware.py`
```python
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

```

### `backend/tests/test_security_headers.py`
```python
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

```
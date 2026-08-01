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

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

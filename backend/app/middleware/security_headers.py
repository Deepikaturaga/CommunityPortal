"""Security-headers middleware (TASK-007 / COMP-012).

Injects on **every** response:
  - Strict-Transport-Security  (HSTS)  — TLS 1.2+ enforcement signal to browsers
  - Content-Security-Policy
  - X-Content-Type-Options
  - X-Frame-Options
  - Referrer-Policy
  - Permissions-Policy
  - Cache-Control               (safe default; callers may override per-route)

It also enforces that inbound requests arrive over HTTPS when the app is deployed
behind a TLS-terminating AWS ALB (https_behind_proxy=True) by inspecting the
X-Forwarded-Proto header.  Non-HTTPS requests receive a 301 redirect so that
HTTP never silently succeeds (OWASP A02 – Cryptographic Failures).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from starlette.datastructures import URL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Routes that must remain exempt from the HTTPS redirect (e.g. ALB health-checks
# arriving over plain HTTP on a private subnet).
_HEALTH_PATHS: frozenset[str] = frozenset({"/health", "/healthz", "/ping"})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers and optionally enforce HTTPS on every response."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._hsts_value = self._build_hsts(settings)
        self._csp_value = settings.csp_policy

    # ── HSTS header value ─────────────────────────────────────────────────────
    @staticmethod
    def _build_hsts(s: Settings) -> str:
        value = f"max-age={s.hsts_max_age}"
        if s.hsts_include_subdomains:
            value += "; includeSubDomains"
        if s.hsts_preload:
            value += "; preload"
        return value

    # ── Middleware dispatch ───────────────────────────────────────────────────
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # ── HTTPS enforcement (ALB proxy mode) ────────────────────────────────
        if self._settings.https_behind_proxy:
            proto = request.headers.get("x-forwarded-proto", "https")
            if proto != "https" and request.url.path not in _HEALTH_PATHS:
                https_url = URL(
                    scope={
                        **request.scope,
                        "scheme": "https",
                    }
                )
                logger.warning("Redirecting insecure request to HTTPS: %s", request.url)
                return RedirectResponse(url=str(https_url), status_code=301)

        response: Response = await call_next(request)
        self._inject_headers(response)
        return response

    # ── Header injection ──────────────────────────────────────────────────────
    def _inject_headers(self, response: Response) -> None:
        h = response.headers

        # Never override headers the route handler has already set explicitly.
        if "strict-transport-security" not in h and self._settings.https_behind_proxy:
            h.append("strict-transport-security", self._hsts_value)

        if "content-security-policy" not in h:
            h.append("content-security-policy", self._csp_value)

        if "x-content-type-options" not in h:
            h.append("x-content-type-options", "nosniff")

        if "x-frame-options" not in h:
            h.append("x-frame-options", "DENY")

        if "referrer-policy" not in h:
            h.append("referrer-policy", "strict-origin-when-cross-origin")

        if "permissions-policy" not in h:
            h.append(
                "permissions-policy",
                "geolocation=(), microphone=(), camera=(), payment=()",
            )

        # Conservative cache default; individual routes can override.
        if "cache-control" not in h:
            h.append("cache-control", "no-store")

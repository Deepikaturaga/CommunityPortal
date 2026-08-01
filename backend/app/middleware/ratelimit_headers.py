"""
Starlette middleware that attaches rate-limit response headers to every
reply that went through a rate-limited route.

Headers added (matching the ``RateLimit-*`` draft standard):
  RateLimit-Limit:     <max requests in window>
  RateLimit-Remaining: <remaining requests>
  RateLimit-Reset:     <seconds until window resets>
  Retry-After:         <seconds> (only on 429)
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """Inject RateLimit-* headers when a route dependency has set them."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[operator]

        limit = getattr(request.state, "ratelimit_limit", None)
        remaining = getattr(request.state, "ratelimit_remaining", None)
        reset = getattr(request.state, "ratelimit_reset", None)

        if limit is not None:
            response.headers["RateLimit-Limit"] = str(limit)
        if remaining is not None:
            response.headers["RateLimit-Remaining"] = str(remaining)
        if reset is not None:
            response.headers["RateLimit-Reset"] = str(reset)
        if response.status_code == 429 and reset is not None:
            response.headers["Retry-After"] = str(reset)

        return response

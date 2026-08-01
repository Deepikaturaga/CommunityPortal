"""
FastAPI dependency factories for per-account rate-limit enforcement.

Usage in a router:

    @router.post("/register")
    async def register(
        body: RegisterRequest,
        _: None = Depends(rate_limit_register),
    ):
        ...

Each dependency reads the current account identifier from either the
request body (registration) or the resolved JWT principal (authenticated
routes).  For anonymous registration/login the *IP address* is used as the
bucket key so that unauthenticated bursts are still bounded.

AC-031.2: all rate-limited routes return 429 with a generic message.
"""

from __future__ import annotations

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.exceptions import RateLimitError
from app.core.redis_client import get_redis
from app.middleware.ratelimit import check_rate_limit

import redis.asyncio as aioredis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client_key(request: Request) -> str:
    """
    Return the best available identifier for the caller.

    Prefer the real IP behind a trusted reverse proxy (X-Forwarded-For first
    header).  Falls back to the direct connection host.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _enforce(
    *,
    request: Request,
    redis: aioredis.Redis,
    settings: Settings,
    account_id: str,
    action: str,
    limit: int,
    window: int,
) -> None:
    """Run the check and raise RateLimitError (AC-031.2) on breach."""
    result = await check_rate_limit(
        redis,
        account_id=account_id,
        action=action,
        limit=limit,
        window_seconds=window,
    )
    # Attach rate-limit headers regardless of outcome so clients can back off.
    request.state.ratelimit_limit = result.limit
    request.state.ratelimit_remaining = result.remaining
    request.state.ratelimit_reset = result.reset_after

    if not result.allowed:
        raise RateLimitError()  # Generic 429 message – AC-031.2


# ---------------------------------------------------------------------------
# Per-route dependency factories
# ---------------------------------------------------------------------------

async def rate_limit_register(
    request: Request,
    redis: aioredis.Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Dependency: enforce registration rate limit.

    Bucket: client IP (unauthenticated at registration time).
    Threshold: RATELIMIT_REGISTER_MAX / RATELIMIT_REGISTER_WINDOW_SECONDS.
    """
    await _enforce(
        request=request,
        redis=redis,
        settings=settings,
        account_id=_client_key(request),
        action="register",
        limit=settings.ratelimit_register_max,
        window=settings.ratelimit_register_window_seconds,
    )


async def rate_limit_login(
    request: Request,
    redis: aioredis.Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Dependency: enforce login rate limit.

    Bucket: client IP.  A successful login does NOT reset the counter –
    credential-stuffing protection requires the window to drain naturally.
    Threshold: RATELIMIT_LOGIN_MAX / RATELIMIT_LOGIN_WINDOW_SECONDS.
    """
    await _enforce(
        request=request,
        redis=redis,
        settings=settings,
        account_id=_client_key(request),
        action="login",
        limit=settings.ratelimit_login_max,
        window=settings.ratelimit_login_window_seconds,
    )


async def rate_limit_content_create(
    request: Request,
    redis: aioredis.Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Dependency: enforce content-creation rate limit.

    Bucket: authenticated account_id extracted from the JWT sub claim that
    must have been validated upstream (e.g. by ``get_current_account``).
    Falls back to IP if account is not on the request state.
    Threshold: RATELIMIT_CONTENT_CREATE_MAX / RATELIMIT_CONTENT_CREATE_WINDOW_SECONDS.
    """
    account_id: str = getattr(request.state, "account_id", None) or _client_key(request)
    await _enforce(
        request=request,
        redis=redis,
        settings=settings,
        account_id=account_id,
        action="content_create",
        limit=settings.ratelimit_content_create_max,
        window=settings.ratelimit_content_create_window_seconds,
    )

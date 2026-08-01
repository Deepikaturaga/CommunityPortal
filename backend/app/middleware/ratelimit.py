"""
Per-account sliding-window rate limiter backed by Redis.

Design:
- Uses Redis atomic INCR + EXPIRE (or Lua script) to track a counter per
  (account_id, action) pair within a configurable window.
- Returns (allowed: bool, remaining: int, reset_after: int) so callers can
  surface Retry-After headers without separate round-trips.
- Falls back to ALLOW on Redis unavailability so a Redis outage does not
  cause a complete auth/write blackout; the fallback is logged as ERROR for
  observability.

AC-031.2: callers raise RateLimitError whose message is generic and does not
reveal internal thresholds to API consumers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lua script: atomic INCR + conditional EXPIRE in one round-trip
# ---------------------------------------------------------------------------
_LUA_INCR_EXPIRE = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))
end
return {current, redis.call('TTL', KEYS[1])}
"""


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    count: int        # current counter value
    limit: int        # configured maximum
    remaining: int    # remaining calls in this window
    reset_after: int  # seconds until the window resets


async def check_rate_limit(
    redis: aioredis.Redis,
    *,
    account_id: str,
    action: str,
    limit: int,
    window_seconds: int,
) -> RateLimitResult:
    """
    Increment the sliding counter for *account_id* + *action* and return a
    RateLimitResult.

    The key format is ``rl:{action}:{account_id}`` to prevent cross-action
    pollution and allow targeted key inspection in ops tooling.
    """
    key = f"rl:{action}:{account_id}"
    try:
        result: list[int] = await redis.eval(  # type: ignore[no-untyped-call]
            _LUA_INCR_EXPIRE, 1, key, window_seconds
        )
        count, ttl = int(result[0]), int(result[1])
        # TTL can be -1 if EXPIRE raced; treat the full window as remaining.
        reset_after = ttl if ttl > 0 else window_seconds
        allowed = count <= limit
        remaining = max(0, limit - count)
        return RateLimitResult(
            allowed=allowed,
            count=count,
            limit=limit,
            remaining=remaining,
            reset_after=reset_after,
        )
    except Exception:
        # Redis unavailable – fail open (log at ERROR for alerting).
        logger.error(
            "Rate-limit Redis unavailable for key=%s action=%s – failing open",
            key,
            action,
        )
        return RateLimitResult(
            allowed=True,
            count=0,
            limit=limit,
            remaining=limit,
            reset_after=window_seconds,
        )

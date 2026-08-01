"""
Unit tests for the rate-limit core logic (check_rate_limit).

Tests:
  - Returns allowed=True while count <= limit
  - Returns allowed=False once count > limit
  - remaining decrements correctly
  - RateLimitResult.reset_after reflects TTL from Redis
  - Fails open (allowed=True) when Redis raises an exception
"""

from __future__ import annotations

import pytest

from app.middleware.ratelimit import RateLimitResult, check_rate_limit
from tests.conftest import FakeRedis


@pytest.mark.asyncio
async def test_allowed_within_limit() -> None:
    redis = FakeRedis()
    result = await check_rate_limit(
        redis, account_id="user1", action="test", limit=5, window_seconds=60
    )
    assert result.allowed is True
    assert result.count == 1
    assert result.remaining == 4
    assert result.limit == 5


@pytest.mark.asyncio
async def test_threshold_hit_returns_denied() -> None:
    redis = FakeRedis()
    for _ in range(5):
        await check_rate_limit(
            redis, account_id="user2", action="test", limit=5, window_seconds=60
        )
    # 6th call exceeds limit=5
    result = await check_rate_limit(
        redis, account_id="user2", action="test", limit=5, window_seconds=60
    )
    assert result.allowed is False
    assert result.count == 6
    assert result.remaining == 0


@pytest.mark.asyncio
async def test_different_accounts_isolated() -> None:
    redis = FakeRedis()
    for _ in range(5):
        await check_rate_limit(
            redis, account_id="userA", action="login", limit=5, window_seconds=60
        )
    # userB should still be allowed
    result = await check_rate_limit(
        redis, account_id="userB", action="login", limit=5, window_seconds=60
    )
    assert result.allowed is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_different_actions_isolated() -> None:
    redis = FakeRedis()
    for _ in range(5):
        await check_rate_limit(
            redis, account_id="user1", action="login", limit=5, window_seconds=60
        )
    # same user, different action → own counter
    result = await check_rate_limit(
        redis, account_id="user1", action="register", limit=5, window_seconds=60
    )
    assert result.allowed is True
    assert result.count == 1


@pytest.mark.asyncio
async def test_fails_open_on_redis_error() -> None:
    """Redis unavailability must not block the caller (fail-open policy)."""

    class BrokenRedis:
        async def eval(self, *args: object, **kwargs: object) -> None:
            raise ConnectionError("Redis down")

    result = await check_rate_limit(
        BrokenRedis(),  # type: ignore[arg-type]
        account_id="user1",
        action="test",
        limit=5,
        window_seconds=60,
    )
    assert result.allowed is True


@pytest.mark.asyncio
async def test_reset_after_reflects_ttl() -> None:
    redis = FakeRedis()
    result = await check_rate_limit(
        redis, account_id="user1", action="test", limit=10, window_seconds=300
    )
    assert result.reset_after == 300

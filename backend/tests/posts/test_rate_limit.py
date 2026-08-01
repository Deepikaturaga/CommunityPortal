"""AC-021 — Rate limiting tests.

Acceptance criteria:
  AC-021.1  After RATE_LIMIT_MAX_POSTS (10) within the window, next POST → 429
  AC-021.2  429 response contains a descriptive detail message
  AC-021.3  Rate limit is per-author: different authors have independent counters
  AC-021.4  Requests to read/list/update/delete do NOT count against post-create limit
  AC-021.5  Service-layer unit test: RateLimitError raised when count >= limit
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services.posts.actions import (
    RATE_LIMIT_MAX_POSTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RateLimitError,
    create_post,
)
from app.services.posts.schemas import PostCreateRequest
from tests.posts.conftest import user_auth_headers


# ---------------------------------------------------------------------------
# Integration tests (HTTP layer)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestRateLimitIntegration:
    """HTTP-layer rate-limit tests via the ASGI test client."""

    async def _flood_create(
        self,
        client: AsyncClient,
        user: User,
        count: int,
    ) -> list[int]:
        """Issue *count* POST /api/v1/posts and return the status codes."""
        status_codes: list[int] = []
        for i in range(count):
            resp = await client.post(
                "/api/v1/posts",
                json={"title": f"Flood post {i}", "body": "body content"},
                headers=user_auth_headers(user),
            )
            status_codes.append(resp.status_code)
        return status_codes

    # ------------------------------------------------------------------
    # AC-021.1  10 succeed, 11th is 429
    # ------------------------------------------------------------------
    async def test_rate_limit_blocks_on_eleventh_post(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        """Create RATE_LIMIT_MAX_POSTS posts — all succeed; the next is 429."""
        codes = await self._flood_create(
            client, regular_user, RATE_LIMIT_MAX_POSTS + 1
        )
        assert all(c == 201 for c in codes[:RATE_LIMIT_MAX_POSTS]), (
            f"First {RATE_LIMIT_MAX_POSTS} should be 201; got {codes[:RATE_LIMIT_MAX_POSTS]}"
        )
        assert codes[RATE_LIMIT_MAX_POSTS] == 429, (
            f"Post #{RATE_LIMIT_MAX_POSTS + 1} should be 429; got {codes[RATE_LIMIT_MAX_POSTS]}"
        )

    # ------------------------------------------------------------------
    # AC-021.2  429 has a descriptive message
    # ------------------------------------------------------------------
    async def test_rate_limit_response_has_detail(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        await self._flood_create(client, regular_user, RATE_LIMIT_MAX_POSTS)
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Over limit", "body": "body"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 429
        body = resp.json()
        assert "detail" in body
        assert len(body["detail"]) > 0

    # ------------------------------------------------------------------
    # AC-021.3  Rate limit is per-author
    # ------------------------------------------------------------------
    async def test_rate_limit_is_per_author(
        self,
        client: AsyncClient,
        regular_user: User,
        other_user: User,
        db_session: AsyncSession,
    ) -> None:
        """Exhaust rate limit for regular_user; other_user is unaffected."""
        await self._flood_create(client, regular_user, RATE_LIMIT_MAX_POSTS)
        # regular_user is now limited
        blocked = await client.post(
            "/api/v1/posts",
            json={"title": "Over limit", "body": "body"},
            headers=user_auth_headers(regular_user),
        )
        assert blocked.status_code == 429

        # other_user is NOT limited
        allowed = await client.post(
            "/api/v1/posts",
            json={"title": "Other user post", "body": "fine"},
            headers=user_auth_headers(other_user),
        )
        assert allowed.status_code == 201

    # ------------------------------------------------------------------
    # AC-021.4  Read/update/delete do NOT count against create limit
    # ------------------------------------------------------------------
    async def test_reads_do_not_count_against_rate_limit(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        """Performing many GET requests should not trigger the create rate limit."""
        for _ in range(RATE_LIMIT_MAX_POSTS + 5):
            await client.get(
                f"/api/v1/posts/{active_post.id}",
                headers=user_auth_headers(regular_user),
            )
        # Creating a post should still succeed (rate limit not consumed)
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "After reads", "body": "body"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Unit tests (service layer)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestRateLimitUnit:
    """Direct service-layer tests; mock the DB to control count output."""

    async def test_rate_limit_error_raised_when_at_limit(self) -> None:
        """AC-021.5 — RateLimitError when recent_count >= RATE_LIMIT_MAX_POSTS."""
        mock_db = AsyncMock()

        # Simulate scalar_one() returning exactly RATE_LIMIT_MAX_POSTS
        scalar_result = MagicMock()
        scalar_result.scalar_one.return_value = RATE_LIMIT_MAX_POSTS
        mock_db.execute.return_value = scalar_result

        with pytest.raises(RateLimitError):
            await create_post(
                mock_db,
                author_id="user-123",
                payload=PostCreateRequest(title="Test", body="body"),
            )

    async def test_rate_limit_error_raised_when_above_limit(self) -> None:
        """RateLimitError when count is already above the limit."""
        mock_db = AsyncMock()
        scalar_result = MagicMock()
        scalar_result.scalar_one.return_value = RATE_LIMIT_MAX_POSTS + 5
        mock_db.execute.return_value = scalar_result

        with pytest.raises(RateLimitError):
            await create_post(
                mock_db,
                author_id="user-456",
                payload=PostCreateRequest(title="Flood", body="body"),
            )

    async def test_no_error_when_below_limit(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        """No error when the author has fewer posts than the limit."""
        # 0 recent posts — should succeed
        payload = PostCreateRequest(title="First post", body="Hello")
        result = await create_post(
            db_session,
            author_id=regular_user.id,
            payload=payload,
        )
        assert result.title == "First post"
        assert result.author_id == regular_user.id

    def test_rate_limit_constants_are_sane(self) -> None:
        """Contract: constants are set to reasonable defaults."""
        assert RATE_LIMIT_MAX_POSTS == 10
        assert RATE_LIMIT_WINDOW_SECONDS == 60

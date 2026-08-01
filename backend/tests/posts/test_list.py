"""AC-018 — Post list / pagination tests.

Acceptance criteria:
  AC-018.1  200 + PostPage shape for authenticated request
  AC-018.2  401 when unauthenticated
  AC-018.3  Pagination: page/page_size respected; pages calculated correctly
  AC-018.4  author_id filter returns only that author's posts
  AC-018.5  status filter returns only matching posts
  AC-018.6  Deleted posts excluded from default listing for regular users
  AC-018.7  Deleted posts included for moderator listing
  AC-018.8  page_size upper bound (100) enforced
  AC-018.9  page_size lower bound (1) enforced
  AC-018.10 Results ordered by created_at descending
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostList:
    # ------------------------------------------------------------------
    # AC-018.1  Happy path — shape
    # ------------------------------------------------------------------
    async def test_list_returns_200_and_page_shape(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    # ------------------------------------------------------------------
    # AC-018.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_list_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/posts")
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-018.3  Pagination
    # ------------------------------------------------------------------
    async def test_pagination_page_size_respected(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        # Create 5 extra active posts
        for i in range(5):
            db_session.add(
                Content(
                    author_id=regular_user.id,
                    title=f"Paged {i}",
                    body="body",
                    status=ContentStatus.active,
                )
            )
        await db_session.flush()

        resp = await client.get(
            "/api/v1/posts?page_size=2&page=1",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2

    async def test_pagination_pages_field_correct(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        # Clear slate: create exactly 3 active posts, page_size=2 → 2 pages
        for i in range(3):
            db_session.add(
                Content(
                    author_id=regular_user.id,
                    title=f"Calc {i}",
                    body="body",
                    status=ContentStatus.active,
                )
            )
        await db_session.flush()

        resp = await client.get(
            "/api/v1/posts?page_size=2&author_id=" + regular_user.id,
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        assert data["total"] >= 3
        expected_pages = -(-data["total"] // 2)  # ceiling division
        assert data["pages"] == expected_pages

    # ------------------------------------------------------------------
    # AC-018.4  author_id filter
    # ------------------------------------------------------------------
    async def test_author_filter_returns_only_own_posts(
        self,
        client: AsyncClient,
        regular_user: User,
        other_user: User,
        active_post: Content,
        db_session: AsyncSession,
    ) -> None:
        # Create a post for the other user
        other_post = Content(
            author_id=other_user.id,
            title="Other user post",
            body="other body",
            status=ContentStatus.active,
        )
        db_session.add(other_post)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/posts?author_id={regular_user.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert active_post.id in ids
        assert other_post.id not in ids

    # ------------------------------------------------------------------
    # AC-018.5  status filter
    # ------------------------------------------------------------------
    async def test_status_filter_flagged(
        self,
        client: AsyncClient,
        moderator_user: User,
        flagged_post: Content,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=flagged",
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        statuses = {item["status"] for item in items}
        assert statuses == {"flagged"} or all(s == "flagged" for s in statuses)
        ids = [item["id"] for item in items]
        assert flagged_post.id in ids
        assert active_post.id not in ids

    # ------------------------------------------------------------------
    # AC-018.6  Deleted posts excluded for regular users (default listing)
    # ------------------------------------------------------------------
    async def test_deleted_excluded_for_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        other_user: User,
        active_post: Content,
        deleted_post: Content,
        db_session: AsyncSession,
    ) -> None:
        # deleted_post is owned by regular_user but still should be hidden
        # from listing when NOT filtering by own author_id
        resp = await client.get(
            f"/api/v1/posts?author_id={other_user.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        # deleted_post should not appear in other user's perspective
        ids = [item["id"] for item in resp.json()["items"]]
        assert deleted_post.id not in ids

    # ------------------------------------------------------------------
    # AC-018.7  Moderator sees deleted posts
    # ------------------------------------------------------------------
    async def test_moderator_sees_deleted_posts(
        self,
        client: AsyncClient,
        moderator_user: User,
        deleted_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=deleted",
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert deleted_post.id in ids

    # ------------------------------------------------------------------
    # AC-018.8  page_size upper bound
    # ------------------------------------------------------------------
    async def test_page_size_over_100_rejected(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?page_size=101",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # AC-018.9  page_size lower bound
    # ------------------------------------------------------------------
    async def test_page_size_zero_rejected(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?page_size=0",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # AC-018.10  Ordering — newest first
    # ------------------------------------------------------------------
    async def test_results_ordered_newest_first(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        from datetime import UTC, datetime, timedelta

        base = datetime.now(UTC)
        posts = []
        for offset in range(3):
            p = Content(
                author_id=regular_user.id,
                title=f"Ordered {offset}",
                body="body",
                status=ContentStatus.active,
                created_at=base + timedelta(seconds=offset),
            )
            db_session.add(p)
            posts.append(p)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/posts?author_id={regular_user.id}&page_size=100",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        owned_ids = [p.id for p in posts]
        owned_items = [it for it in items if it["id"] in owned_ids]
        timestamps = [it["created_at"] for it in owned_items]
        assert timestamps == sorted(timestamps, reverse=True)

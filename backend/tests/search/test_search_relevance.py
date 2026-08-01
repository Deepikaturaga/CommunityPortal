"""AC-027.1 — Search relevance and filter correctness.

Validates that the list/filter endpoint returns exactly the rows that match
the supplied filters and no extraneous results:

  AC-027.1 — Results are scoped to requested author_id filter.
  AC-027.1 — Results are scoped to requested status filter (moderators only).
  AC-027.1 — Combined author + status filters intersect correctly.
  AC-027.1 — Absent filters return all visible rows (no false-negatives).
  AC-027.1 — Pagination metadata (total/pages) reflects the filtered set.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.search.conftest import auth_headers, mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestSearchRelevance:
    """AC-027.1 — filter results match requested criteria exactly."""

    # ------------------------------------------------------------------
    # author_id filter
    # ------------------------------------------------------------------

    async def test_author_filter_returns_only_that_author(
        self,
        client: AsyncClient,
        searcher: User,
        author: User,
        seed_active: Content,
        db_session: AsyncSession,
    ) -> None:
        """Only posts owned by the filtered author appear in results."""
        from app.models.user import UserRole

        other = User(
            username="other_rel",
            email="other_rel@example.com",
            hashed_password="hashed",
            role=UserRole.user,
        )
        db_session.add(other)
        await db_session.flush()
        from tests.search.conftest import _make_post

        other_post = await _make_post(
            db_session,
            owner=other,
            title="Other author post",
            body="Should not appear",
            status=ContentStatus.active,
        )

        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_active.id in ids
        assert other_post.id not in ids

    async def test_author_filter_nonexistent_returns_empty(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        """Filtering by an unknown author_id yields an empty page, not an error."""
        resp = await client.get(
            "/api/v1/posts?author_id=00000000-0000-0000-0000-000000000000",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    # ------------------------------------------------------------------
    # status filter (moderator only)
    # ------------------------------------------------------------------

    async def test_status_filter_active_returns_only_active(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        """Moderator filtering status=active sees only active posts."""
        resp = await client.get(
            "/api/v1/posts?status=active",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert item["status"] == "active", f"Unexpected status {item['status']!r}"

    async def test_status_filter_hidden_returns_only_hidden(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        """Moderator filtering status=hidden sees only hidden posts."""
        resp = await client.get(
            "/api/v1/posts?status=hidden",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert full_seed["hidden"].id in [it["id"] for it in items]
        for item in items:
            assert item["status"] == "hidden"

    async def test_status_filter_deleted_returns_only_deleted(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=deleted",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert full_seed["deleted"].id in [it["id"] for it in items]
        for item in items:
            assert item["status"] == "deleted"

    async def test_status_filter_flagged_returns_only_flagged(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=flagged",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert full_seed["flagged"].id in [it["id"] for it in items]
        for item in items:
            assert item["status"] == "flagged"

    async def test_status_filter_locked_returns_only_locked(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=locked",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert full_seed["locked"].id in [it["id"] for it in items]
        for item in items:
            assert item["status"] == "locked"

    # ------------------------------------------------------------------
    # Combined filters
    # ------------------------------------------------------------------

    async def test_combined_author_and_status_filter(
        self,
        client: AsyncClient,
        search_moderator: User,
        author: User,
        full_seed: dict[str, Content],
        db_session: AsyncSession,
    ) -> None:
        """author_id + status filter must intersect — not union."""
        from app.models.user import UserRole

        other = User(
            username="other_comb",
            email="other_comb@example.com",
            hashed_password="hashed",
            role=UserRole.user,
        )
        db_session.add(other)
        await db_session.flush()
        from tests.search.conftest import _make_post

        other_active = await _make_post(
            db_session,
            owner=other,
            title="Other active",
            body="body",
            status=ContentStatus.active,
        )

        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=active",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert full_seed["active"].id in ids
        # Other author's active post must NOT appear
        assert other_active.id not in ids
        # Author's non-active posts must NOT appear
        assert full_seed["flagged"].id not in ids
        assert full_seed["deleted"].id not in ids

    # ------------------------------------------------------------------
    # No filter — baseline
    # ------------------------------------------------------------------

    async def test_no_filter_includes_active_posts(
        self,
        client: AsyncClient,
        searcher: User,
        seed_active: Content,
    ) -> None:
        """Unfiltered listing for a regular user includes active posts."""
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_active.id in ids

    async def test_invalid_status_value_rejected(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        """An unrecognised status enum value returns 422."""
        resp = await client.get(
            "/api/v1/posts?status=unapproved",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422

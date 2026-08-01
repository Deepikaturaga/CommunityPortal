"""AC-017 — Post read (single) tests.

Acceptance criteria:
  AC-017.1  200 + PostOut for existing active post
  AC-017.2  401 when unauthenticated
  AC-017.3  Deleted post → 404 for regular users
  AC-017.4  Deleted post → 200 for moderators / admins
  AC-017.5  Response fields match DB record exactly
  AC-017.6  404 for completely non-existent ID
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.content import Content
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostRead:
    # ------------------------------------------------------------------
    # AC-017.1  Happy path
    # ------------------------------------------------------------------
    async def test_get_active_post_200(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == active_post.id
        assert data["title"] == active_post.title
        assert data["body"] == active_post.body

    # ------------------------------------------------------------------
    # AC-017.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_get_post_requires_auth(
        self,
        client: AsyncClient,
        active_post: Content,
    ) -> None:
        resp = await client.get(f"/api/v1/posts/{active_post.id}")
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-017.3  Deleted post hidden from regular users
    # ------------------------------------------------------------------
    async def test_deleted_post_is_404_for_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        deleted_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{deleted_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # AC-017.4  Deleted post visible to moderators
    # ------------------------------------------------------------------
    async def test_deleted_post_visible_to_moderator(
        self,
        client: AsyncClient,
        moderator_user: User,
        deleted_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{deleted_post.id}",
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    # ------------------------------------------------------------------
    # AC-017.5  Response fields match DB
    # ------------------------------------------------------------------
    async def test_response_fields_match_db(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        assert data["id"] == active_post.id
        assert data["author_id"] == active_post.author_id
        assert data["title"] == active_post.title
        assert data["body"] == active_post.body
        assert data["status"] == active_post.status.value
        assert data["is_locked"] == active_post.is_locked

    # ------------------------------------------------------------------
    # AC-017.6  Non-existent ID → 404
    # ------------------------------------------------------------------
    async def test_nonexistent_post_404(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts/does-not-exist-at-all",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # Cross-user read (regular user may read other users' active posts)
    # ------------------------------------------------------------------
    async def test_other_user_can_read_active_post(
        self,
        client: AsyncClient,
        other_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(other_user),
        )
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # Flagged / locked posts are readable by regular users (only deleted
    # content is hidden).
    # ------------------------------------------------------------------
    async def test_flagged_post_readable_by_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        flagged_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{flagged_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200

    async def test_locked_post_readable_by_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        locked_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{locked_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200

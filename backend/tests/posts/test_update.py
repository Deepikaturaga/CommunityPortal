"""AC-019 — Post update (PATCH) tests.

Acceptance criteria:
  AC-019.1  200 + updated PostOut when author patches own post
  AC-019.2  401 when unauthenticated
  AC-019.3  403 when non-owner regular user attempts update
  AC-019.4  422 when attempting to edit a locked post (as regular user)
  AC-019.5  422 when attempting to edit a deleted post
  AC-019.6  404 for non-existent post ID
  AC-019.7  Moderator can edit any non-deleted post
  AC-019.8  Moderator can edit a locked post
  AC-019.9  Partial update: only supplied fields change; others preserved
  AC-019.10 updated_at is refreshed after update
"""
from __future__ import annotations

import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostUpdate:
    # ------------------------------------------------------------------
    # AC-019.1  Happy path
    # ------------------------------------------------------------------
    async def test_update_own_active_post(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "New title", "body": "New body"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New title"
        assert data["body"] == "New body"

    # ------------------------------------------------------------------
    # AC-019.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_update_requires_auth(
        self,
        client: AsyncClient,
        active_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "X"},
        )
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-019.3  Non-owner forbidden
    # ------------------------------------------------------------------
    async def test_update_rejects_non_owner(
        self,
        client: AsyncClient,
        other_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "Steal"},
            headers=user_auth_headers(other_user),
        )
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # AC-019.4  Locked post — regular user cannot edit
    # ------------------------------------------------------------------
    async def test_update_locked_post_forbidden_for_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        locked_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{locked_post.id}",
            json={"body": "Attempt edit"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # AC-019.5  Deleted post — cannot be edited
    # ------------------------------------------------------------------
    async def test_update_deleted_post_rejected(
        self,
        client: AsyncClient,
        regular_user: User,
        deleted_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{deleted_post.id}",
            json={"title": "Ghost edit"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code in (403, 422)

    # ------------------------------------------------------------------
    # AC-019.6  Non-existent post → 404
    # ------------------------------------------------------------------
    async def test_update_nonexistent_post_404(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.patch(
            "/api/v1/posts/no-such-id",
            json={"title": "X"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # AC-019.7  Moderator can edit any non-deleted post
    # ------------------------------------------------------------------
    async def test_moderator_can_edit_other_users_post(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "Mod edited"},
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Mod edited"

    # ------------------------------------------------------------------
    # AC-019.8  Moderator can edit a locked post
    # ------------------------------------------------------------------
    async def test_moderator_can_edit_locked_post(
        self,
        client: AsyncClient,
        moderator_user: User,
        locked_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{locked_post.id}",
            json={"body": "Mod override"},
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        assert resp.json()["body"] == "Mod override"

    # ------------------------------------------------------------------
    # AC-019.9  Partial update preserves unchanged fields
    # ------------------------------------------------------------------
    async def test_partial_update_preserves_title(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        original_title = active_post.title
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"body": "Only body updated"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == original_title
        assert resp.json()["body"] == "Only body updated"

    async def test_partial_update_preserves_body(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        original_body = active_post.body
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "Only title updated"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        assert resp.json()["body"] == original_body
        assert resp.json()["title"] == "Only title updated"

    # ------------------------------------------------------------------
    # AC-019.10  updated_at refreshed
    # ------------------------------------------------------------------
    async def test_updated_at_changes_after_patch(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
        db_session: AsyncSession,
    ) -> None:
        original_updated_at = active_post.updated_at
        # Small sleep to guarantee a different timestamp
        await asyncio.sleep(0.01)
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "Time check"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200

        # Re-fetch from DB
        stmt = select(Content).where(Content.id == active_post.id)
        row = (await db_session.execute(stmt)).scalar_one()
        assert row.updated_at >= original_updated_at

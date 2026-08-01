"""AC-020 — Post soft-delete tests.

Acceptance criteria:
  AC-020.1  204 No Content on successful delete
  AC-020.2  401 when unauthenticated
  AC-020.3  403 when non-owner regular user attempts delete
  AC-020.4  404 for non-existent post
  AC-020.5  post.status becomes "deleted" in DB after delete
  AC-020.6  Idempotent: deleting an already-deleted post returns 204
  AC-020.7  Moderator can delete any post
  AC-020.8  Deleted post is no longer visible to regular users (GET → 404)
  AC-020.9  Hard delete of DB row is NOT allowed — row persists after soft-delete
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostDelete:
    # ------------------------------------------------------------------
    # AC-020.1  Happy path — 204
    # ------------------------------------------------------------------
    async def test_delete_own_post_returns_204(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 204
        assert resp.content == b""

    # ------------------------------------------------------------------
    # AC-020.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_delete_requires_auth(
        self,
        client: AsyncClient,
        active_post: Content,
    ) -> None:
        resp = await client.delete(f"/api/v1/posts/{active_post.id}")
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-020.3  Non-owner forbidden
    # ------------------------------------------------------------------
    async def test_delete_rejects_non_owner(
        self,
        client: AsyncClient,
        other_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(other_user),
        )
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # AC-020.4  Non-existent post → 404
    # ------------------------------------------------------------------
    async def test_delete_nonexistent_post_404(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.delete(
            "/api/v1/posts/totally-fake-id",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # AC-020.5  Status becomes "deleted" in DB
    # ------------------------------------------------------------------
    async def test_delete_sets_status_deleted_in_db(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
        db_session: AsyncSession,
    ) -> None:
        await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        stmt = select(Content).where(Content.id == active_post.id)
        row = (await db_session.execute(stmt)).scalar_one()
        assert row.status == ContentStatus.deleted

    # ------------------------------------------------------------------
    # AC-020.6  Idempotent — re-deleting returns 204
    # ------------------------------------------------------------------
    async def test_delete_idempotent(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp1 = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        resp2 = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp1.status_code == 204
        assert resp2.status_code == 204

    # ------------------------------------------------------------------
    # AC-020.7  Moderator can delete any post
    # ------------------------------------------------------------------
    async def test_moderator_can_delete_any_post(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 204

    # ------------------------------------------------------------------
    # AC-020.8  Deleted post becomes 404 for regular users
    # ------------------------------------------------------------------
    async def test_deleted_post_returns_404_on_get(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        get_resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert get_resp.status_code == 404

    # ------------------------------------------------------------------
    # AC-020.9  Row persists after soft-delete (no hard delete)
    # ------------------------------------------------------------------
    async def test_row_persists_after_soft_delete(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
        db_session: AsyncSession,
    ) -> None:
        await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        stmt = select(Content).where(Content.id == active_post.id)
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None, "Row must still exist after soft-delete"
        assert row.status == ContentStatus.deleted

    # ------------------------------------------------------------------
    # Deleting a flagged post works (not only active)
    # ------------------------------------------------------------------
    async def test_can_delete_flagged_post(
        self,
        client: AsyncClient,
        regular_user: User,
        flagged_post: Content,
        db_session: AsyncSession,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{flagged_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 204
        stmt = select(Content).where(Content.id == flagged_post.id)
        row = (await db_session.execute(stmt)).scalar_one()
        assert row.status == ContentStatus.deleted

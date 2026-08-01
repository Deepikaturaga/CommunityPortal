"""
HTTP integration tests for posts endpoints — draft visibility & ownership.

VER-002 (HTTP layer): GET /api/v1/posts/{id} returns 404 for draft to non-owner
VER-004 (HTTP layer): PATCH/DELETE returns 403 for non-owner on published post,
                      404 for non-owner on draft (existence not leaked)
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.post import Post
from app.models.user import User
from tests.conftest import bearer


@pytest.mark.asyncio
class TestDraftVisibilityHTTP:
    """VER-002: Draft post 404 to unauthenticated + non-owner callers."""

    async def test_draft_unauthenticated_returns_404(
        self, client: AsyncClient, draft_post: Post
    ) -> None:
        resp = await client.get(f"/api/v1/posts/{draft_post.id}")
        assert resp.status_code == 404

    async def test_draft_non_owner_returns_404(
        self,
        client: AsyncClient,
        draft_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{draft_post.id}", headers=bearer(other_author_user)
        )
        assert resp.status_code == 404

    async def test_draft_owner_returns_200(
        self,
        client: AsyncClient,
        draft_post: Post,
        author_user: User,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{draft_post.id}", headers=bearer(author_user)
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(draft_post.id)

    async def test_draft_admin_returns_200(
        self,
        client: AsyncClient,
        draft_post: Post,
        admin_user: User,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{draft_post.id}", headers=bearer(admin_user)
        )
        assert resp.status_code == 200

    async def test_published_unauthenticated_returns_200(
        self, client: AsyncClient, published_post: Post
    ) -> None:
        resp = await client.get(f"/api/v1/posts/{published_post.id}")
        assert resp.status_code == 200

    async def test_list_excludes_drafts_for_unauthenticated(
        self,
        client: AsyncClient,
        draft_post: Post,
        published_post: Post,
    ) -> None:
        resp = await client.get("/api/v1/posts")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(published_post.id) in ids
        assert str(draft_post.id) not in ids

    async def test_list_includes_own_draft_for_author(
        self,
        client: AsyncClient,
        draft_post: Post,
        published_post: Post,
        author_user: User,
    ) -> None:
        resp = await client.get("/api/v1/posts", headers=bearer(author_user))
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(draft_post.id) in ids

    async def test_list_excludes_others_drafts_for_different_author(
        self,
        client: AsyncClient,
        draft_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.get("/api/v1/posts", headers=bearer(other_author_user))
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(draft_post.id) not in ids

    async def test_list_includes_all_drafts_for_admin(
        self,
        client: AsyncClient,
        draft_post: Post,
        admin_user: User,
    ) -> None:
        resp = await client.get("/api/v1/posts", headers=bearer(admin_user))
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(draft_post.id) in ids


@pytest.mark.asyncio
class TestOwnershipEnforcementHTTP:
    """VER-004: PATCH/DELETE ownership checks."""

    async def test_owner_can_patch_own_post(
        self,
        client: AsyncClient,
        published_post: Post,
        author_user: User,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{published_post.id}",
            json={"title": "Updated title"},
            headers=bearer(author_user),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated title"

    async def test_non_owner_patch_published_returns_403(
        self,
        client: AsyncClient,
        published_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{published_post.id}",
            json={"title": "Stolen edit"},
            headers=bearer(other_author_user),
        )
        assert resp.status_code == 403

    async def test_non_owner_patch_draft_returns_404(
        self,
        client: AsyncClient,
        draft_post: Post,
        other_author_user: User,
    ) -> None:
        """Non-owner patching a draft should receive 404, not 403 (draft existence hidden)."""
        resp = await client.patch(
            f"/api/v1/posts/{draft_post.id}",
            json={"title": "Stolen edit"},
            headers=bearer(other_author_user),
        )
        assert resp.status_code == 404

    async def test_admin_can_patch_any_post(
        self,
        client: AsyncClient,
        published_post: Post,
        admin_user: User,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{published_post.id}",
            json={"title": "Admin override"},
            headers=bearer(admin_user),
        )
        assert resp.status_code == 200

    async def test_owner_can_delete_own_post(
        self,
        client: AsyncClient,
        published_post: Post,
        author_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{published_post.id}", headers=bearer(author_user)
        )
        assert resp.status_code == 204

    async def test_non_owner_delete_published_returns_403(
        self,
        client: AsyncClient,
        published_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{published_post.id}", headers=bearer(other_author_user)
        )
        assert resp.status_code == 403

    async def test_non_owner_delete_draft_returns_404(
        self,
        client: AsyncClient,
        draft_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{draft_post.id}", headers=bearer(other_author_user)
        )
        assert resp.status_code == 404

    async def test_admin_can_delete_any_post(
        self,
        client: AsyncClient,
        published_post: Post,
        admin_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{published_post.id}", headers=bearer(admin_user)
        )
        assert resp.status_code == 204

    async def test_unauthenticated_patch_returns_401(
        self, client: AsyncClient, published_post: Post
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{published_post.id}", json={"title": "x"}
        )
        assert resp.status_code == 401

    async def test_unauthenticated_delete_returns_401(
        self, client: AsyncClient, published_post: Post
    ) -> None:
        resp = await client.delete(f"/api/v1/posts/{published_post.id}")
        assert resp.status_code == 401

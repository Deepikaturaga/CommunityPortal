"""AC-017/AC-018 — Contract tests.

Verify that the HTTP response shapes exactly match the declared Pydantic schemas
(PostOut, PostPage) so that the API contract is honoured end-to-end.

VER-002 — Response schema matches OpenAPI/Pydantic model.
VER-020 — All required fields present with correct types.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services.posts.schemas import PostOut, PostPage
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostContractSinglePost:
    """Contract: GET /api/v1/posts/{id} response matches PostOut."""

    async def test_response_validates_as_post_out(
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
        # Validate against Pydantic model — raises ValidationError on mismatch
        post = PostOut.model_validate(resp.json())
        assert post.id == active_post.id

    async def test_post_out_required_fields_present(
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
        required_fields = {"id", "author_id", "title", "body", "status", "is_locked", "created_at", "updated_at"}
        assert required_fields.issubset(data.keys()), (
            f"Missing fields: {required_fields - data.keys()}"
        )

    async def test_post_out_field_types(
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
        assert isinstance(data["id"], str)
        assert isinstance(data["author_id"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["body"], str)
        assert data["status"] in [s.value for s in ContentStatus]
        assert isinstance(data["is_locked"], bool)
        # ISO-8601 datetime strings
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    async def test_status_enum_values_are_valid(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_post: Content,
        flagged_post: Content,
        locked_post: Content,
        deleted_post: Content,
    ) -> None:
        valid_statuses = {s.value for s in ContentStatus}
        for post in (active_post, flagged_post, locked_post, deleted_post):
            resp = await client.get(
                f"/api/v1/posts/{post.id}",
                headers=mod_auth_headers(moderator_user),
            )
            assert resp.status_code == 200
            assert resp.json()["status"] in valid_statuses


@pytest.mark.asyncio
class TestPostContractListPage:
    """Contract: GET /api/v1/posts response matches PostPage."""

    async def test_response_validates_as_post_page(
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
        page = PostPage.model_validate(resp.json())
        assert isinstance(page.items, list)
        assert isinstance(page.total, int)
        assert page.total >= 0

    async def test_post_page_required_fields(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        required = {"items", "total", "page", "page_size", "pages"}
        assert required.issubset(data.keys())

    async def test_post_page_items_are_post_out(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        for item in data["items"]:
            PostOut.model_validate(item)  # must not raise

    async def test_post_page_pagination_fields_types(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?page=1&page_size=5",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)
        assert isinstance(data["pages"], int)
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["pages"] >= 1

    async def test_create_response_validates_as_post_out(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Contract check", "body": "body text"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        PostOut.model_validate(resp.json())  # must not raise

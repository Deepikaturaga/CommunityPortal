"""AC-016 — Post creation tests.

Acceptance criteria:
  AC-016.1  201 + PostOut on valid request
  AC-016.2  401 when unauthenticated
  AC-016.3  422 when title is missing / blank
  AC-016.4  422 when body is missing / blank
  AC-016.5  Title and body are persisted to DB correctly
  AC-016.6  author_id is taken from the JWT (not the request body)
  AC-016.7  New post has status=active, is_locked=False
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
class TestPostCreate:
    # ------------------------------------------------------------------
    # AC-016.1  Happy path
    # ------------------------------------------------------------------
    async def test_create_returns_201_and_post_shape(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "My first post", "body": "Hello everyone!"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My first post"
        assert data["body"] == "Hello everyone!"
        assert data["author_id"] == regular_user.id
        assert data["status"] == "active"
        assert data["is_locked"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    # ------------------------------------------------------------------
    # AC-016.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_create_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "No auth", "body": "body"},
        )
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-016.3  Missing / blank title
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "payload",
        [
            {"body": "No title here"},
            {"title": "", "body": "blank title"},
            {"title": "   ", "body": "whitespace title"},
        ],
    )
    async def test_create_rejects_invalid_title(
        self,
        client: AsyncClient,
        regular_user: User,
        payload: dict,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json=payload,
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # AC-016.4  Missing / blank body
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "payload",
        [
            {"title": "No body"},
            {"title": "Empty body", "body": ""},
            {"title": "Whitespace body", "body": "   "},
        ],
    )
    async def test_create_rejects_invalid_body(
        self,
        client: AsyncClient,
        regular_user: User,
        payload: dict,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json=payload,
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # AC-016.5  Persistence
    # ------------------------------------------------------------------
    async def test_create_persists_to_db(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Persisted", "body": "Check DB"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        post_id = resp.json()["id"]
        stmt = select(Content).where(Content.id == post_id)
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.title == "Persisted"
        assert row.body == "Check DB"

    # ------------------------------------------------------------------
    # AC-016.6  author_id from JWT
    # ------------------------------------------------------------------
    async def test_author_id_comes_from_jwt(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "JWT author", "body": "must match"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        assert resp.json()["author_id"] == regular_user.id

    # ------------------------------------------------------------------
    # AC-016.7  Default status / lock
    # ------------------------------------------------------------------
    async def test_create_default_status_and_lock(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Defaults", "body": "status check"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == ContentStatus.active.value
        assert data["is_locked"] is False

    # ------------------------------------------------------------------
    # Moderator can also create posts (extended happy path)
    # ------------------------------------------------------------------
    async def test_moderator_can_create_post(
        self,
        client: AsyncClient,
        moderator_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Mod post", "body": "Written by mod"},
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 201
        assert resp.json()["author_id"] == moderator_user.id

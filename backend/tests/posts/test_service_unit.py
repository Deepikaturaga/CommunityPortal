"""VER-010 — Service-layer unit tests.

Tests that exercise the business-logic functions directly (no HTTP), mocking
the database where needed.  These cover error paths, edge cases, and domain
invariants that are difficult to reproduce through the HTTP layer alone.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services.posts.actions import (
    PostDeletedError,
    PostForbiddenError,
    PostNotFoundError,
    create_post,
    delete_post,
    get_post,
    list_posts,
    update_post,
)
from app.services.posts.schemas import PostCreateRequest, PostUpdateRequest


@pytest.mark.asyncio
class TestCreatePostUnit:
    async def test_create_returns_post_out(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        payload = PostCreateRequest(title="Unit title", body="Unit body")
        result = await create_post(db_session, author_id=regular_user.id, payload=payload)
        assert result.title == "Unit title"
        assert result.body == "Unit body"
        assert result.author_id == regular_user.id
        assert result.status == ContentStatus.active
        assert result.is_locked is False

    async def test_create_post_id_is_uuid_like(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        payload = PostCreateRequest(title="ID check", body="body")
        result = await create_post(db_session, author_id=regular_user.id, payload=payload)
        assert len(result.id) == 36  # UUID4 string length
        assert result.id.count("-") == 4


@pytest.mark.asyncio
class TestGetPostUnit:
    async def test_get_nonexistent_raises(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        with pytest.raises(PostNotFoundError):
            await get_post(
                db_session,
                post_id="no-such-post",
                caller_id=regular_user.id,
                caller_role="user",
            )

    async def test_get_deleted_raises_for_regular_user(
        self,
        db_session: AsyncSession,
        regular_user: User,
        deleted_post: Content,
    ) -> None:
        with pytest.raises(PostNotFoundError):
            await get_post(
                db_session,
                post_id=deleted_post.id,
                caller_id=regular_user.id,
                caller_role="user",
            )

    async def test_get_deleted_succeeds_for_moderator(
        self,
        db_session: AsyncSession,
        moderator_user: User,
        deleted_post: Content,
    ) -> None:
        result = await get_post(
            db_session,
            post_id=deleted_post.id,
            caller_id=moderator_user.id,
            caller_role="moderator",
        )
        assert result.status == ContentStatus.deleted


@pytest.mark.asyncio
class TestUpdatePostUnit:
    async def test_update_nonexistent_raises(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        with pytest.raises(PostNotFoundError):
            await update_post(
                db_session,
                post_id="ghost",
                caller_id=regular_user.id,
                caller_role="user",
                payload=PostUpdateRequest(title="X"),
            )

    async def test_update_deleted_raises(
        self,
        db_session: AsyncSession,
        regular_user: User,
        deleted_post: Content,
    ) -> None:
        with pytest.raises(PostDeletedError):
            await update_post(
                db_session,
                post_id=deleted_post.id,
                caller_id=regular_user.id,
                caller_role="user",
                payload=PostUpdateRequest(title="edit deleted"),
            )

    async def test_update_other_users_post_raises(
        self,
        db_session: AsyncSession,
        other_user: User,
        active_post: Content,
    ) -> None:
        with pytest.raises(PostForbiddenError):
            await update_post(
                db_session,
                post_id=active_post.id,
                caller_id=other_user.id,
                caller_role="user",
                payload=PostUpdateRequest(title="steal"),
            )

    async def test_update_locked_raises_for_user(
        self,
        db_session: AsyncSession,
        regular_user: User,
        locked_post: Content,
    ) -> None:
        with pytest.raises(PostForbiddenError):
            await update_post(
                db_session,
                post_id=locked_post.id,
                caller_id=regular_user.id,
                caller_role="user",
                payload=PostUpdateRequest(body="attempt"),
            )

    async def test_update_locked_succeeds_for_moderator(
        self,
        db_session: AsyncSession,
        moderator_user: User,
        locked_post: Content,
    ) -> None:
        result = await update_post(
            db_session,
            post_id=locked_post.id,
            caller_id=moderator_user.id,
            caller_role="moderator",
            payload=PostUpdateRequest(body="mod override"),
        )
        assert result.body == "mod override"


@pytest.mark.asyncio
class TestDeletePostUnit:
    async def test_delete_nonexistent_raises(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        with pytest.raises(PostNotFoundError):
            await delete_post(
                db_session,
                post_id="ghost",
                caller_id=regular_user.id,
                caller_role="user",
            )

    async def test_delete_other_users_post_raises(
        self,
        db_session: AsyncSession,
        other_user: User,
        active_post: Content,
    ) -> None:
        with pytest.raises(PostForbiddenError):
            await delete_post(
                db_session,
                post_id=active_post.id,
                caller_id=other_user.id,
                caller_role="user",
            )

    async def test_delete_sets_status(
        self,
        db_session: AsyncSession,
        regular_user: User,
        active_post: Content,
    ) -> None:
        await delete_post(
            db_session,
            post_id=active_post.id,
            caller_id=regular_user.id,
            caller_role="user",
        )
        await db_session.refresh(active_post)
        assert active_post.status == ContentStatus.deleted

    async def test_delete_idempotent(
        self,
        db_session: AsyncSession,
        regular_user: User,
        active_post: Content,
    ) -> None:
        await delete_post(
            db_session,
            post_id=active_post.id,
            caller_id=regular_user.id,
            caller_role="user",
        )
        # Second call must not raise
        await delete_post(
            db_session,
            post_id=active_post.id,
            caller_id=regular_user.id,
            caller_role="user",
        )
        await db_session.refresh(active_post)
        assert active_post.status == ContentStatus.deleted


@pytest.mark.asyncio
class TestListPostsUnit:
    async def test_list_returns_page_structure(
        self,
        db_session: AsyncSession,
        regular_user: User,
        active_post: Content,
    ) -> None:
        page = await list_posts(
            db_session,
            caller_id=regular_user.id,
            caller_role="user",
        )
        assert page.page == 1
        assert page.page_size == 20
        assert page.total >= 1
        assert any(item.id == active_post.id for item in page.items)

    async def test_list_excludes_deleted_for_user(
        self,
        db_session: AsyncSession,
        regular_user: User,
        other_user: User,
        deleted_post: Content,
    ) -> None:
        page = await list_posts(
            db_session,
            caller_id=other_user.id,
            caller_role="user",
            author_id=other_user.id,
        )
        ids = [item.id for item in page.items]
        assert deleted_post.id not in ids

    async def test_list_includes_deleted_for_moderator(
        self,
        db_session: AsyncSession,
        moderator_user: User,
        deleted_post: Content,
    ) -> None:
        page = await list_posts(
            db_session,
            caller_id=moderator_user.id,
            caller_role="moderator",
            status_filter=ContentStatus.deleted,
        )
        ids = [item.id for item in page.items]
        assert deleted_post.id in ids

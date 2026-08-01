from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user import User
    from app.schemas.posts import PostCreate, PostUpdate

    async def get_by_id(self, post_id: uuid.UUID, viewer: "User | None") -> Post:
    async def get_by_slug(self, slug: str, viewer: "User | None") -> Post:
        viewer: "User | None",
            pass  # no filter -- admin sees all
    async def create(self, data: "PostCreate", author: "User") -> Post:
        data: "PostUpdate",
        editor: "User",
    async def delete(self, post_id: uuid.UUID, actor: "User") -> None:
"""Post service — thin persistence layer consumed by routers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PostStatus
from app.models.post import Post
from app.services.posts.visibility import assert_post_visible, assert_post_visible_and_editable


class PostService:
    """CRUD operations for posts with integrated visibility enforcement."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

        """Return *post_id* if *viewer* may see it, else raise HTTP 404."""
        result = await self._db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        return assert_post_visible(post, viewer)

        """Return the post with *slug* if *viewer* may see it, else raise HTTP 404."""
        result = await self._db.execute(select(Post).where(Post.slug == slug))
        post = result.scalar_one_or_none()
        return assert_post_visible(post, viewer)

    async def list_visible(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Post]:
        """
        Return posts the *viewer* is allowed to see.

        - Unauthenticated or READER users: published posts only.
        - AUTHOR: published posts + own drafts.
        - ADMIN: all posts.
        """
        stmt = select(Post).order_by(Post.created_at.desc()).limit(limit).offset(offset)

        if viewer is None:
            stmt = stmt.where(Post.status == PostStatus.PUBLISHED)
        elif viewer.role.value == "admin":
        else:
            # author sees their own drafts + all published
            from sqlalchemy import or_

            stmt = stmt.where(
                or_(
                    Post.status == PostStatus.PUBLISHED,
                    (Post.status == PostStatus.DRAFT) & (Post.author_id == viewer.id),
                )
            )

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

        post = Post(
            title=data.title,
            slug=data.slug,
            body=data.body,
            status=data.status,
            author_id=author.id,
        )
        self._db.add(post)
        await self._db.flush()
        await self._db.refresh(post)
        return post

    async def update(
        self,
        post_id: uuid.UUID,
    ) -> Post:
        """Update a post — raises 404 if not visible, 403 if not owner/admin."""
        result = await self._db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        post = assert_post_visible_and_editable(post, editor)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)

        await self._db.flush()
        await self._db.refresh(post)
        return post

        """Delete a post — raises 404 if not visible, 403 if not owner/admin."""
        result = await self._db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        post = assert_post_visible_and_editable(post, actor)
        await self._db.delete(post)
        await self._db.flush()

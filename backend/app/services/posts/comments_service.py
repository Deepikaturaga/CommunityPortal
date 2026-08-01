"""
Comment service — business logic for TASK-042.

Responsibilities:
1. Verify the target Post exists (raises 404 otherwise).
2. Persist the Comment in a single explicit transaction.
3. Emit IF-017 CommentCreatedEvent after successful persistence.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.events.publisher import EventPublisher
from app.services.posts.comment_model import Comment
from app.services.posts.comments_schema import (
    CommentCreate,
    CommentCreatedEvent,
    CommentResponse,
)
from app.services.posts.models import Post

log = get_logger(__name__)


class CommentService:
    def __init__(self, session: AsyncSession, publisher: EventPublisher) -> None:
        self._session = session
        self._publisher = publisher

    # ── Queries ──────────────────────────────────────────────────────────────

    async def _get_post_or_404(self, post_id: uuid.UUID) -> Post:
        result = await self._session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post {post_id} not found",
            )
        return post

    # ── Commands ─────────────────────────────────────────────────────────────

    async def create_comment(
        self,
        post_id: uuid.UUID,
        author_id: uuid.UUID,
        payload: CommentCreate,
    ) -> CommentResponse:
        """
        Persist comment + emit IF-017 event.

        Transaction is committed before the event fires so the DB write is
        durable even if the event bus is temporarily unavailable.
        """
        post = await self._get_post_or_404(post_id)

        comment = Comment(
            id=uuid.uuid4(),
            post_id=post_id,
            author_id=author_id,
            body=payload.body,
        )
        async with self._session.begin():
            self._session.add(comment)

        # Refresh to pick up server-side defaults (created_at, updated_at)
        await self._session.refresh(comment)

        log.info(
            "comment.created",
            comment_id=str(comment.id),
            post_id=str(post_id),
            author_id=str(author_id),
        )

        # ── IF-017 event emission ────────────────────────────────────────────
        event = CommentCreatedEvent(
            comment_id=comment.id,
            post_id=post_id,
            author_id=author_id,
            post_author_id=post.author_id,
            body_preview=comment.body[:200],
            occurred_at=comment.created_at if comment.created_at else datetime.now(UTC),
        )
        await self._publisher.publish(event.event_type, event.model_dump(mode="json"))

        return CommentResponse.model_validate(comment)

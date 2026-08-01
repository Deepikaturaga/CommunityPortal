"""
Router: POST /posts/{post_id}/comments

Requires Bearer JWT auth (deny-by-default).
B008 (Depends in default) is intentional FastAPI pattern — suppressed per ruff config.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.core.database import get_session
from app.events.publisher import EventPublisher, get_event_publisher
from app.services.posts.comments_schema import CommentCreate, CommentResponse
from app.services.posts.comments_service import CommentService

router = APIRouter(prefix="/posts", tags=["comments"])


def _get_comment_service(
    session: AsyncSession = Depends(get_session),  # noqa: B008
    publisher: EventPublisher = Depends(get_event_publisher),  # noqa: B008
) -> CommentService:
    return CommentService(session=session, publisher=publisher)


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment on a post",
    description=(
        "Persists the comment and emits a `comment.created` event (IF-017) "
        "for downstream notification consumers."
    ),
)
async def create_comment(
    post_id: UUID,
    body: CommentCreate,
    current_user_id: UUID = Depends(get_current_user_id),  # noqa: B008
    service: CommentService = Depends(_get_comment_service),  # noqa: B008
) -> CommentResponse:
    return await service.create_comment(
        post_id=post_id,
        author_id=current_user_id,
        payload=body,
    )

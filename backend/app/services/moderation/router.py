"""Moderation review queue & actions router (TASK-037 / IF-009).

Endpoints:
  GET  /api/v1/moderation/queue          — list flagged/pending content items
  POST /api/v1/moderation/queue/{id}/actions — apply lock / hide / delete

Both endpoints require the `moderator` or `admin` role (403 otherwise — AC-014.3).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, require_moderator
from app.models.content import ContentStatus
from app.services.moderation.actions import (
    ContentNotFoundError,
    InvalidTransitionError,
    apply_action,
    list_queue,
)
from app.services.moderation.schemas import (
    ModerationActionRequest,
    ModerationActionResponse,
    QueuePage,
)

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.get(
    "/queue",
    response_model=QueuePage,
    status_code=status.HTTP_200_OK,
    summary="List moderation review queue",
    description=(
        "Returns a paginated list of content items with the given status "
        "(default: flagged). Requires moderator or admin role."
    ),
)
async def get_queue(
    queue_status: ContentStatus = Query(
        default=ContentStatus.flagged,
        alias="status",
        description="Filter by content status",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    _moderator: TokenPayload = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
) -> QueuePage:
    return await list_queue(db, status=queue_status, page=page, page_size=page_size)


@router.post(
    "/queue/{content_id}/actions",
    response_model=ModerationActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply a moderation action",
    description=(
        "Issue a lock, hide, or delete command to a content item (COMP-003). "
        "Writes an immutable audit record on every action (AC-014.3/4). "
        "Requires moderator or admin role."
    ),
)
async def post_action(
    content_id: str,
    body: ModerationActionRequest,
    moderator: TokenPayload = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
) -> ModerationActionResponse:
    try:
        return await apply_action(
            db,
            content_id=content_id,
            moderator_id=moderator.sub,
            action=body.action,
            reason=body.reason,
        )
    except ContentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

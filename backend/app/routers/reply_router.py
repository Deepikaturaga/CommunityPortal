from __future__ import annotations

# Reply HTTP router — mounts under /api/v1/discussions/{discussion_id}/replies
# POST /              → create reply (AC-010 length, AC-012 lock/hide)
# GET  /              → list replies (AC-012.3 hide-state filtering)
# PATCH /{reply_id}   → edit own reply (AC-013.2 auth, AC-013.3 moderator)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import get_current_user_id, get_is_moderator
from app.services.discussion import replies as reply_service
from app.services.discussion.exceptions import (
    DiscussionHiddenError,
    DiscussionLockedError,
    DiscussionNotFoundError,
    ReplyBodyTooLongError,
    ReplyBodyTooShortError,
    ReplyForbiddenError,
    ReplyHiddenError,
    ReplyNotFoundError,
)
from app.services.discussion.schemas import ReplyCreate, ReplyResponse, ReplyUpdate

router = APIRouter(
    prefix="/discussions/{discussion_id}/replies",
    tags=["replies"],
)


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, DiscussionNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found.")
    if isinstance(exc, DiscussionLockedError):
        # AC-010.2: locked thread → 423 Locked
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="This discussion is locked and no longer accepts replies.",
        )
    if isinstance(exc, DiscussionHiddenError):
        # Opaque 404 — must not reveal hidden status to non-moderators (AC-012.3)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion not found.",
        )
    if isinstance(exc, ReplyNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found.")
    if isinstance(exc, ReplyForbiddenError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to modify this reply.",
        )
    if isinstance(exc, ReplyHiddenError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found.")
    if isinstance(exc, ReplyBodyTooShortError | ReplyBodyTooLongError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    raise exc


@router.post(
    "",
    response_model=ReplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reply on a discussion (AC-010, AC-012)",
)
async def create_reply(
    discussion_id: int,
    payload: ReplyCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReplyResponse:
    try:
        reply = await reply_service.create_reply(
            db,
            discussion_id=discussion_id,
            author_id=current_user_id,
            body=payload.body,
            min_length=settings.reply_min_length,
            max_length=settings.reply_max_length,
        )
    except Exception as exc:
        _handle_service_error(exc)
    return ReplyResponse.model_validate(reply)


@router.get(
    "",
    response_model=list[ReplyResponse],
    status_code=status.HTTP_200_OK,
    summary="List visible replies for a discussion (AC-012.3 hide-state filtering)",
)
async def list_replies(
    discussion_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    is_moderator: bool = Depends(get_is_moderator),
) -> list[ReplyResponse]:
    try:
        replies_list = await reply_service.list_replies(
            db,
            discussion_id=discussion_id,
            include_hidden=is_moderator,  # AC-012.3 / AC-013.3
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        _handle_service_error(exc)
    return [ReplyResponse.model_validate(r) for r in replies_list]


@router.get(
    "/{reply_id}",
    response_model=ReplyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single reply",
)
async def get_reply(
    discussion_id: int,
    reply_id: int,
    db: AsyncSession = Depends(get_db),
    is_moderator: bool = Depends(get_is_moderator),
) -> ReplyResponse:
    try:
        reply = await reply_service.get_reply(
            db,
            discussion_id=discussion_id,
            reply_id=reply_id,
            include_hidden=is_moderator,
        )
    except Exception as exc:
        _handle_service_error(exc)
    return ReplyResponse.model_validate(reply)


@router.patch(
    "/{reply_id}",
    response_model=ReplyResponse,
    status_code=status.HTTP_200_OK,
    summary="Edit own reply (AC-013.2 edit authorisation)",
)
async def update_reply(
    discussion_id: int,
    reply_id: int,
    payload: ReplyUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReplyResponse:
    try:
        reply = await reply_service.update_reply(
            db,
            discussion_id=discussion_id,
            reply_id=reply_id,
            requesting_user_id=current_user_id,
            new_body=payload.body,
            min_length=settings.reply_min_length,
            max_length=settings.reply_max_length,
        )
    except Exception as exc:
        _handle_service_error(exc)
    return ReplyResponse.model_validate(reply)

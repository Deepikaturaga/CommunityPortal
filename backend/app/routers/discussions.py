from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_admin
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.discussion_schemas import (
    DiscussionCreateRequest,
    DiscussionUpdateRequest,
    DiscussionResponse,
    PostCreateRequest,
    PostUpdateRequest,
    PostResponse,
)
from app.services import discussion_service

router = APIRouter(prefix="/discussions", tags=["discussions"])


def _err(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=DiscussionResponse, status_code=status.HTTP_201_CREATED)
async def create_discussion(
    req: DiscussionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.create_discussion(db, current_user, req)
    except AppError as e:
        raise _err(e)


@router.get("", response_model=dict)
async def list_discussions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    items, total = await discussion_service.list_discussions(db, page, page_size, status_filter)
    from app.schemas.discussion_schemas import DiscussionResponse as DR
    return {
        "items": [DR.model_validate(d).model_dump() for d in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{discussion_id}", response_model=DiscussionResponse)
async def get_discussion(discussion_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await discussion_service.get_discussion(db, discussion_id)
    except AppError as e:
        raise _err(e)


@router.put("/{discussion_id}", response_model=DiscussionResponse)
async def update_discussion(
    discussion_id: int,
    req: DiscussionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.update_discussion(db, current_user, discussion_id, req)
    except AppError as e:
        raise _err(e)


@router.delete("/{discussion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discussion(
    discussion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await discussion_service.delete_discussion(db, current_user, discussion_id)
    except AppError as e:
        raise _err(e)


# ── Posts ──────────────────────────────────────────────────────────────────

posts_router = APIRouter(prefix="/discussions/{discussion_id}/posts", tags=["posts"])


@posts_router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    discussion_id: int,
    req: PostCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.create_post(db, current_user, discussion_id, req)
    except AppError as e:
        raise _err(e)


@posts_router.get("", response_model=dict)
async def list_posts(
    discussion_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await discussion_service.list_posts(db, discussion_id, page, page_size)
    from app.schemas.discussion_schemas import PostResponse as PR
    return {
        "items": [PR.model_validate(p).model_dump() for p in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@posts_router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    discussion_id: int,
    post_id: int,
    req: PostUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.update_post(db, current_user, post_id, req)
    except AppError as e:
        raise _err(e)


@posts_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    discussion_id: int,
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await discussion_service.delete_post(db, current_user, post_id)
    except AppError as e:
        raise _err(e)


@posts_router.post("/{post_id}/accept", response_model=PostResponse)
async def accept_answer(
    discussion_id: int,
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.mark_accepted_answer(db, current_user, discussion_id, post_id)
    except AppError as e:
        raise _err(e)

"""Posts REST API router with visibility enforcement."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user, get_optional_user
from app.models.user import User
from app.schemas.posts import PostCreate, PostRead, PostUpdate
from app.services.posts.service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


def _svc(db: AsyncSession = Depends(get_db)) -> PostService:
    return PostService(db)


@router.get("", response_model=list[PostRead])
async def list_posts(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    viewer: User | None = Depends(get_optional_user),
    svc: PostService = Depends(_svc),
) -> list[PostRead]:
    posts = await svc.list_visible(viewer, limit=limit, offset=offset)
    return [PostRead.model_validate(p) for p in posts]


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate,
    author: User = Depends(get_current_active_user),
    svc: PostService = Depends(_svc),
) -> PostRead:
    post = await svc.create(data, author)
    return PostRead.model_validate(post)


@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    svc: PostService = Depends(_svc),
) -> PostRead:
    post = await svc.get_by_id(post_id, viewer)
    return PostRead.model_validate(post)


@router.patch("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: uuid.UUID,
    data: PostUpdate,
    editor: User = Depends(get_current_active_user),
    svc: PostService = Depends(_svc),
) -> PostRead:
    post = await svc.update(post_id, data, editor)
    return PostRead.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_post(
    post_id: uuid.UUID,
    actor: User = Depends(get_current_active_user),
    svc: PostService = Depends(_svc),
) -> None:
    await svc.delete(post_id, actor)

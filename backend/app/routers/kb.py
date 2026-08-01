from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.kb_schemas import (
    KBArticleCreateRequest,
    KBArticleUpdateRequest,
    KBArticleResponse,
)
from app.services import kb_service

router = APIRouter(prefix="/kb", tags=["knowledge-base"])


def _err(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=KBArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    req: KBArticleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await kb_service.create_article(db, current_user, req)
    except AppError as e:
        raise _err(e)


@router.get("", response_model=dict)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    items, total = await kb_service.list_articles(db, page, page_size, status_filter, category)
    return {
        "items": [KBArticleResponse.model_validate(a).model_dump() for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/slug/{slug}", response_model=KBArticleResponse)
async def get_article_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    try:
        return await kb_service.get_article_by_slug(db, slug)
    except AppError as e:
        raise _err(e)


@router.get("/{article_id}", response_model=KBArticleResponse)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await kb_service.get_article(db, article_id)
    except AppError as e:
        raise _err(e)


@router.put("/{article_id}", response_model=KBArticleResponse)
async def update_article(
    article_id: int,
    req: KBArticleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await kb_service.update_article(db, current_user, article_id, req)
    except AppError as e:
        raise _err(e)


@router.post("/{article_id}/publish", response_model=KBArticleResponse)
async def publish_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await kb_service.publish_article(db, current_user, article_id)
    except AppError as e:
        raise _err(e)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await kb_service.delete_article(db, current_user, article_id)
    except AppError as e:
        raise _err(e)

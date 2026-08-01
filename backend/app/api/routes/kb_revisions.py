"""
REST router for KB revision history (IF-006).

Endpoints
---------
GET /kb/articles/{article_id}/revisions
    Paginated list — author / moderator / admin only (AC-026.2)

GET /kb/articles/{article_id}/revisions/{revision_id}
    Single revision — same ACL
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.kb_revision_schema import KBRevisionListResponse, KBRevisionRead
from app.services.kb import revisions as revision_service

router = APIRouter(
    prefix="/kb/articles/{article_id}/revisions",
    tags=["kb-revisions"],
)


@router.get(
    "",
    response_model=KBRevisionListResponse,
    summary="List revision history for a KB article",
    responses={
        403: {"description": "Not the article author, moderator, or admin"},
        404: {"description": "Article not found"},
    },
)
async def list_revisions(
    article_id: int,
    page: int = Query(default=1, ge=1, description="1-based page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> KBRevisionListResponse:
    """Return paginated revision history.  Access: author (own articles), moderator, admin."""
    return await revision_service.get_revisions(
        db,
        article_id=article_id,
        current_user=current_user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{revision_id}",
    response_model=KBRevisionRead,
    summary="Fetch a single KB article revision",
    responses={
        403: {"description": "Not the article author, moderator, or admin"},
        404: {"description": "Revision or article not found"},
    },
)
async def get_revision(
    article_id: int,
    revision_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> KBRevisionRead:
    """Retrieve one immutable revision snapshot.  Access: author (own articles), moderator, admin."""
    return await revision_service.get_revision_by_id(
        db,
        article_id=article_id,
        revision_id=revision_id,
        current_user=current_user,
    )

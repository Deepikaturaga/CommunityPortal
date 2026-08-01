"""FastAPI router for the posts service.

Endpoints:
  POST   /api/v1/posts            — create   (AC-016)
  GET    /api/v1/posts/{id}       — read     (AC-017)
  GET    /api/v1/posts            — list     (AC-018)
  PATCH  /api/v1/posts/{id}       — update   (AC-019)
  DELETE /api/v1/posts/{id}       — delete   (AC-020)

Rate limiting is enforced inside the service layer (AC-021).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user_payload
from app.models.content import ContentStatus
from app.services.posts.actions import (
    PostDeletedError,
    PostForbiddenError,
    PostNotFoundError,
    RateLimitError,
    create_post,
    delete_post,
    get_post,
    list_posts,
    update_post,
)
from app.services.posts.schemas import PostCreateRequest, PostOut, PostPage, PostUpdateRequest

router = APIRouter(prefix="/posts", tags=["posts"])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=PostOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post (AC-016)",
)
async def create_post_endpoint(
    body: PostCreateRequest,
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> PostOut:
    try:
        return await create_post(db, author_id=caller.sub, payload=body)
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc


# ---------------------------------------------------------------------------
# Read single
# ---------------------------------------------------------------------------


@router.get(
    "/{post_id}",
    response_model=PostOut,
    status_code=status.HTTP_200_OK,
    summary="Get a single post (AC-017)",
)
async def get_post_endpoint(
    post_id: str,
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> PostOut:
    try:
        return await get_post(
            db, post_id=post_id, caller_id=caller.sub, caller_role=caller.role
        )
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PostPage,
    status_code=status.HTTP_200_OK,
    summary="List posts with pagination (AC-018)",
)
async def list_posts_endpoint(
    author_id: str | None = Query(default=None),
    post_status: ContentStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> PostPage:
    return await list_posts(
        db,
        caller_id=caller.sub,
        caller_role=caller.role,
        author_id=author_id,
        status_filter=post_status,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@router.patch(
    "/{post_id}",
    response_model=PostOut,
    status_code=status.HTTP_200_OK,
    summary="Update post title / body (AC-019)",
)
async def update_post_endpoint(
    post_id: str,
    body: PostUpdateRequest,
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> PostOut:
    try:
        return await update_post(
            db,
            post_id=post_id,
            caller_id=caller.sub,
            caller_role=caller.role,
            payload=body,
        )
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PostDeletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except PostForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a post (AC-020)",
)
async def delete_post_endpoint(
    post_id: str,
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await delete_post(
            db,
            post_id=post_id,
            caller_id=caller.sub,
            caller_role=caller.role,
        )
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PostForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

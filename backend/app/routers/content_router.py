"""
Content router: CRUD for content items.

POST /content (create) is guarded by rate_limit_content_create (TASK-058).
The dependency reads request.state.account_id set by get_current_account.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dependencies.auth_deps import get_current_account
from app.middleware.ratelimit_deps import rate_limit_content_create
from app.models.account import Account
from app.schemas.content_schema import (
    ContentCreateRequest,
    ContentResponse,
    ContentUpdateRequest,
)
from app.services.content_service import (
    create_content,
    get_content,
    list_content,
    update_content,
)

router = APIRouter(prefix="/content", tags=["content"])


@router.post(
    "",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a content item",
    dependencies=[Depends(rate_limit_content_create)],
)
async def create(
    body: ContentCreateRequest,
    current_account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_async_session),
) -> ContentResponse:
    item = await create_content(db, str(current_account.id), body)
    return ContentResponse.model_validate(item)


@router.get(
    "",
    response_model=list[ContentResponse],
    status_code=status.HTTP_200_OK,
    summary="List content items for the authenticated account",
)
async def list_items(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_async_session),
) -> list[ContentResponse]:
    items = await list_content(db, str(current_account.id), limit=limit, offset=offset)
    return [ContentResponse.model_validate(i) for i in items]


@router.get(
    "/{content_id}",
    response_model=ContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single content item",
)
async def get_item(
    content_id: str,
    current_account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_async_session),
) -> ContentResponse:
    item = await get_content(db, content_id, str(current_account.id))
    return ContentResponse.model_validate(item)


@router.patch(
    "/{content_id}",
    response_model=ContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a content item",
)
async def update_item(
    content_id: str,
    body: ContentUpdateRequest,
    current_account: Account = Depends(get_current_account),
    db: AsyncSession = Depends(get_async_session),
) -> ContentResponse:
    item = await update_content(db, content_id, str(current_account.id), body)
    return ContentResponse.model_validate(item)

"""
Content service: create and retrieve content items with owner-scoped access.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.content import ContentItem
from app.schemas.content_schema import ContentCreateRequest, ContentUpdateRequest


async def create_content(
    db: AsyncSession,
    owner_id: str,
    req: ContentCreateRequest,
) -> ContentItem:
    item = ContentItem(
        owner_id=owner_id,
        title=req.title,
        body=req.body,
        status=req.status,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_content(
    db: AsyncSession,
    content_id: str,
    owner_id: str,
) -> ContentItem:
    result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_id)
    )
    item: ContentItem | None = result.scalar_one_or_none()
    if item is None:
        raise NotFoundError("Content item not found")
    if str(item.owner_id) != str(owner_id):
        raise ForbiddenError("Access denied")
    return item


async def list_content(
    db: AsyncSession,
    owner_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[ContentItem]:
    result = await db.execute(
        select(ContentItem)
        .where(ContentItem.owner_id == owner_id)
        .order_by(ContentItem.created_at.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )
    return list(result.scalars().all())


async def update_content(
    db: AsyncSession,
    content_id: str,
    owner_id: str,
    req: ContentUpdateRequest,
) -> ContentItem:
    item = await get_content(db, content_id, owner_id)
    if req.title is not None:
        item.title = req.title
    if req.body is not None:
        item.body = req.body
    if req.status is not None:
        item.status = req.status
    await db.commit()
    await db.refresh(item)
    return item

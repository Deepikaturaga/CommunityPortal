from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.misc_schemas import NotificationResponse, NotificationMarkReadRequest
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _err(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("", response_model=dict)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total = await notification_service.list_notifications(
        db, current_user, page, page_size, unread_only
    )
    return {
        "items": [NotificationResponse.model_validate(n).model_dump() for n in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "unread_count": await notification_service.get_unread_count(db, current_user),
    }


@router.post("/mark-read", status_code=status.HTTP_200_OK)
async def mark_read(
    req: NotificationMarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = await notification_service.mark_read(db, current_user, req.notification_ids)
    return {"marked": count}


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = await notification_service.mark_all_read(db, current_user)
    return {"marked": count}


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = await notification_service.get_unread_count(db, current_user)
    return {"unread_count": count}

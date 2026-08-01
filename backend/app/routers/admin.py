from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.misc_schemas import AuditLogResponse
from app.schemas.user_schemas import UserResponse
from app.services import audit_service, user_service

router = APIRouter(prefix="/admin", tags=["admin"])


def _err(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/users", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    from sqlalchemy import func
    count_q = select(func.count(User.id))
    total = (await db.execute(count_q)).scalar_one()
    q = select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = list((await db.execute(q)).scalars().all())
    return {
        "items": [UserResponse.model_validate(u).model_dump() for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        user = await user_service.admin_set_user_active(db, user_id, True)
        await audit_service.record(
            db, "admin.user.activate", actor=admin,
            resource_type="user", resource_id=str(user_id)
        )
        return user
    except AppError as e:
        raise _err(e)


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        user = await user_service.admin_set_user_active(db, user_id, False)
        await audit_service.record(
            db, "admin.user.deactivate", actor=admin,
            resource_type="user", resource_id=str(user_id)
        )
        return user
    except AppError as e:
        raise _err(e)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def set_user_role(
    user_id: int,
    role: str = Query(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        user = await user_service.admin_set_user_role(db, user_id, role)
        await audit_service.record(
            db, "admin.user.role_change", actor=admin,
            resource_type="user", resource_id=str(user_id), detail=f"role={role}"
        )
        return user
    except AppError as e:
        raise _err(e)


@router.get("/audit-logs", response_model=dict)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = None,
    actor_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    items, total = await audit_service.list_audit_logs(db, page, page_size, action, actor_id)
    return {
        "items": [AuditLogResponse.model_validate(a).model_dump() for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    from sqlalchemy import func
    from app.models.discussion import Discussion
    from app.models.post import Post
    from app.models.kb_article import KBArticle

    user_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    disc_count = (await db.execute(select(func.count(Discussion.id)))).scalar_one()
    post_count = (await db.execute(select(func.count(Post.id)))).scalar_one()
    kb_count = (await db.execute(select(func.count(KBArticle.id)))).scalar_one()
    return {
        "users": user_count,
        "discussions": disc_count,
        "posts": post_count,
        "kb_articles": kb_count,
    }

"""Admin router – /api/v1/admin endpoints.

Authorization matrix:
  GET    /admin/users          → ADMIN, SUPERADMIN
  POST   /admin/users          → SUPERADMIN only
  PATCH  /admin/users/{id}     → ADMIN (role/is_active), SUPERADMIN
  DELETE /admin/users/{id}     → SUPERADMIN only
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_min_role, require_role
from app.auth.passwords import hash_password
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user_schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead], summary="List all users")
async def list_users(
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user (superadmin only)",
)
async def create_user(
    body: UserCreate,
    _caller: User = Depends(require_role(UserRole.SUPERADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        hashed_password=hash_password(body.password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserRead, summary="Update a user")
async def update_user(
    user_id: str,
    body: UserUpdate,
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (superadmin only)",
)
async def delete_user(
    user_id: str,
    _caller: User = Depends(require_role(UserRole.SUPERADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()

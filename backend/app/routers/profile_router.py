"""Profile router – /api/v1/profile endpoints.

Authorization matrix:
  GET    /profile/me       → any authenticated user (all 5 roles)
  PATCH  /profile/me       → any authenticated user (self-service: full_name only)
  GET    /profile/{id}     → ADMIN, SUPERADMIN only
  DELETE /profile/{id}     → SUPERADMIN only
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_min_role, require_role
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user_schemas import UserProfileUpdate, UserRead

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=UserRead, summary="Get own profile")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """All authenticated roles can read their own profile."""
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead, summary="Update own profile")
async def update_my_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """All authenticated roles can update their own full_name."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return UserRead.model_validate(current_user)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get any user profile (admin+)",
)
async def get_profile_by_id(
    user_id: str,
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """ADMIN and SUPERADMIN can look up any user profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any user profile (superadmin only)",
)
async def delete_profile(
    user_id: str,
    _caller: User = Depends(require_role(UserRole.SUPERADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Only SUPERADMIN can delete a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token_safe
from app.models.user import User, UserRole
from app.schemas.user_schemas import UserRegisterRequest, UserLoginRequest, UserUpdateRequest, PasswordChangeRequest


async def register_user(db: AsyncSession, req: UserRegisterRequest) -> User:
    # duplicate check
    existing = await db.execute(
        select(User).where((User.email == req.email) | (User.username == req.username))
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Email or username already registered")

    user = User(
        email=req.email,
        username=req.username,
        display_name=req.display_name,
        hashed_password=hash_password(req.password),
        role=UserRole.member.value,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, req: UserLoginRequest) -> tuple[str, str]:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise ForbiddenError("Invalid credentials")
    if not user.is_active:
        raise ForbiddenError("Account is disabled")
    access = create_access_token(str(user.id), {"role": user.role})
    refresh = create_refresh_token(str(user.id))
    return access, refresh


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    payload = decode_token_safe(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise ForbiddenError("Invalid refresh token")
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise ForbiddenError("User not found or inactive")
    access = create_access_token(str(user.id), {"role": user.role})
    new_refresh = create_refresh_token(str(user.id))
    return access, new_refresh


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    return user


async def update_user_profile(db: AsyncSession, user: User, req: UserUpdateRequest) -> User:
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.bio is not None:
        user.bio = req.bio
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    db.add(user)
    await db.flush()
    return user


async def change_password(db: AsyncSession, user: User, req: PasswordChangeRequest) -> None:
    if not verify_password(req.current_password, user.hashed_password):
        raise ForbiddenError("Current password is incorrect")
    user.hashed_password = hash_password(req.new_password)
    db.add(user)
    await db.flush()


async def admin_set_user_active(db: AsyncSession, target_id: int, is_active: bool) -> User:
    user = await get_user_by_id(db, target_id)
    user.is_active = is_active
    db.add(user)
    await db.flush()
    return user


async def admin_set_user_role(db: AsyncSession, target_id: int, role: str) -> User:
    if role not in [r.value for r in UserRole]:
        raise ConflictError(f"Invalid role: {role}")
    user = await get_user_by_id(db, target_id)
    user.role = role
    db.add(user)
    await db.flush()
    return user

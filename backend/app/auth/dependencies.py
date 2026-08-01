"""FastAPI dependencies for authentication and role-based authorization."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.enums import UserRole
from app.models.user import User

_bearer = HTTPBearer(auto_error=True)

_ROLE_RANK: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.CONTRIBUTOR: 1,
    UserRole.EDITOR: 2,
    UserRole.ADMIN: 3,
    UserRole.SUPERADMIN: 4,
}


async def _get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(creds.credentials)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# Convenience typed alias
get_current_user = _get_current_user


def require_role(*roles: UserRole):
    """Return a dependency that enforces the caller has one of the given roles."""

    async def _check(current_user: User = Depends(_get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role}' is not authorised for this operation. "
                    f"Required: {[r.value for r in roles]}"
                ),
            )
        return current_user

    return _check


def require_min_role(min_role: UserRole):
    """Return a dependency that enforces the caller's role rank >= min_role rank."""

    async def _check(current_user: User = Depends(_get_current_user)) -> User:
        if _ROLE_RANK[current_user.role] < _ROLE_RANK[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role}' insufficient. "
                    f"Minimum required: '{min_role.value}'"
                ),
            )
        return current_user

    return _check

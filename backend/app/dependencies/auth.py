"""FastAPI dependency: resolve the currently-authenticated user from a Bearer JWT."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the User whose JWT is supplied, or raise 401."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exc
        user_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the current user; raises 401 if inactive."""
    return current_user


async def get_optional_user(
    token: str | None = Depends(
        OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return the current user if a valid token is present, else None."""
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        sub: str | None = payload.get("sub")
        if sub is None:
            return None
        user_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user

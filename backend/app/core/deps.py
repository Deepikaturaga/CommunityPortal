from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> "User":  # noqa: F821
    from app.models.user import User  # lazy import to avoid circular

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        sub: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if sub is None or token_type != "access":
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == int(sub)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


async def get_current_active_user(
    current_user: "User" = Depends(get_current_user),  # noqa: F821
) -> "User":  # noqa: F821
    return current_user


async def require_admin(
    current_user: "User" = Depends(get_current_user),  # noqa: F821
) -> "User":  # noqa: F821
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

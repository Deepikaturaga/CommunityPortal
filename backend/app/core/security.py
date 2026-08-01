"""JWT-based authentication utilities and FastAPI security dependencies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenData(BaseModel):
    sub: str
    role: str = "viewer"


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def _decode_token(token: str) -> TokenData:
    settings = get_settings()
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str | None = payload.get("sub")
        role: str = payload.get("role", "viewer")
        if sub is None:
            raise credentials_exc
        return TokenData(sub=sub, role=role)
    except JWTError as exc:
        raise credentials_exc from exc


async def get_current_user(token: str = Depends(_oauth2_scheme)) -> TokenData:
    """FastAPI dependency — returns the validated token payload."""
    return _decode_token(token)


async def get_current_editor(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """Restrict to users with role `editor` or `admin`."""
    if current_user.role not in ("editor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user

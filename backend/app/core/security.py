"""JWT auth utilities — token creation and verification."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenPayload(BaseModel):
    sub: str  # user_id as string
    role: str


def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user_payload(
    token: str = Depends(oauth2_scheme),
) -> TokenPayload:
    """Decode + validate JWT; raise 401 on any failure."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = raw.get("sub")
        role: str | None = raw.get("role")
        if user_id is None or role is None:
            raise credentials_exc
        return TokenPayload(sub=user_id, role=role)
    except JWTError:
        raise credentials_exc


async def require_moderator(
    payload: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> TokenPayload:
    """Dependency: allow only users with role == 'moderator' or 'admin'."""
    if payload.role not in ("moderator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator role required",
        )
    return payload

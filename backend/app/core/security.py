    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenPayload(BaseModel):
    sub: str
    role: str


def create_access_token(user_id: str, role: str) -> str:
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = raw.get("sub")
        role = raw.get("role")
        if user_id is None or role is None:
            raise credentials_exc
        return TokenPayload(sub=user_id, role=role)
    except JWTError:
        raise credentials_exc


async def require_moderator(
    payload: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> TokenPayload:
    if payload.role not in ("moderator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Moderator role required"
        )
    return payload


async def get_optional_user_payload(
    request: Request,
) -> Optional[TokenPayload]:
    """Return the caller's ``TokenPayload`` if a valid Bearer token is present,
    otherwise return ``None`` (no error).

    Used by the KB visibility endpoint (AC-025.3): anonymous / non-privileged
    callers receive 404 for non-approved articles; privileged callers see all.
    The function never raises — an invalid or absent token simply yields ``None``.
    """
    auth_header: str | None = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer ") :]
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = raw.get("sub")
        role: str | None = raw.get("role")
        if user_id is None or role is None:
            return None
        return TokenPayload(sub=user_id, role=role)
    except JWTError:
        return None

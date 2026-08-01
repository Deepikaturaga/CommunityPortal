"""JWT authentication helpers."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenPayload(BaseModel):
    sub: str  # user UUID as string
    exp: datetime


def create_access_token(
    subject: UUID | str,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(UTC) + delta
    data: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(
        data,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> UUID:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
        )
        raw_sub: str | None = payload.get("sub")
        if raw_sub is None:
            raise credentials_exc
        return UUID(raw_sub)
    except (JWTError, ValueError) as exc:
        raise credentials_exc from exc

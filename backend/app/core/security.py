from __future__ import annotations

from datetime import datetime, timezone

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(data: dict[str, object], settings: Settings) -> str:
    from datetime import timedelta

    payload = data.copy()
    expire = _utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload["exp"] = expire
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> int:
    """Return the authenticated user's integer ID from the JWT, or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return int(sub)
    except (JWTError, ValueError):
        raise credentials_exception


async def get_is_moderator(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> bool:
    """Return True when the JWT carries role=moderator (AC-013.3).

    Missing or invalid tokens are treated as non-moderator (False) rather than
    raising 401, because listing endpoints are readable without elevated rights.
    Token validation still uses the same secret so forged tokens cannot elevate privilege.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return str(payload.get("role", "")).lower() == "moderator"
    except (JWTError, ValueError):
        return False

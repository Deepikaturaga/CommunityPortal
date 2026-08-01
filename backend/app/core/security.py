from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenPayload:
    """Thin wrapper for JWT claims – no DB round-trip."""

    def __init__(self, sub: str, exp: int) -> None:
        self.user_id: str = sub
        self.exp: int = exp


def _decode_token(token: str) -> TokenPayload:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        sub: str | None = payload.get("sub")
        exp: int | None = payload.get("exp")
        if sub is None or exp is None:
            raise credentials_exc
        if datetime.fromtimestamp(exp, tz=UTC) < datetime.now(tz=UTC):
            raise credentials_exc
        return TokenPayload(sub=sub, exp=exp)
    except JWTError:
        raise credentials_exc from None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenPayload:
    return _decode_token(token)


CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]

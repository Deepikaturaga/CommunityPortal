from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.models.user import UserRole

_bearer = HTTPBearer(auto_error=True)


class TokenPayload:
    def __init__(self, sub: str, role: str) -> None:
        self.sub = sub
        self.role = UserRole(role)


def _extract_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> TokenPayload:
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    sub: str | None = payload.get("sub")
    role: str | None = payload.get("role")
    if not sub or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return TokenPayload(sub=sub, role=role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid role in token",
        ) from exc


CurrentUser = Annotated[TokenPayload, Depends(_extract_token)]


def require_admin(current_user: CurrentUser) -> TokenPayload:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


AdminUser = Annotated[TokenPayload, Depends(require_admin)]

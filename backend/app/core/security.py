"""Auth dependencies — stub until the full auth module (PHASE-011) is wired in.

In production this verifies a JWT, loads the user from DB, and enforces role.
The `require_admin` dependency raises 403 for non-admin callers.
"""

from __future__ import annotations

import enum
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


class UserRole(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"


class CurrentUser:
    def __init__(self, user_id: int, role: UserRole) -> None:
        self.user_id = user_id
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.admin


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    """Stub: accept any bearer token as an admin for development.

    Replace this body with real JWT validation when PHASE-011 auth is available.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # TODO(PHASE-011): validate JWT, load user from DB
    return CurrentUser(user_id=1, role=UserRole.admin)


async def require_admin(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required.",
        )
    return current_user

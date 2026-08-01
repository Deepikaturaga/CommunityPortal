"""JWT creation/verification utilities.

Roles are intentionally NOT embedded in the token payload.
The token carries only the user's stable `sub` (user_id).
The caller re-fetches the current role from the database on every request,
so any admin-driven role change takes effect immediately without re-login.

See AC-032.1 / AC-032.2.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

_ALGORITHM = settings.algorithm


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Return a signed JWT containing *only* the subject (user_id).

    Role is deliberately excluded from the payload so that role changes
    propagate on the very next request without requiring a new token.
    """
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": user_id, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> str:
    """Decode and verify *token*; return the user_id (``sub`` claim).

    Raises :class:`jose.JWTError` on invalid / expired tokens.
    """
    data = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    user_id: str | None = data.get("sub")
    if not user_id:
        raise JWTError("Missing 'sub' claim")
    return user_id

"""Cognito JWT authentication dependency — IF-004 / OWASP A07.

This module defines the ``CognitoUser`` value object and the
``get_current_user`` FastAPI dependency used by all protected routers.

The implementation here is a **stub** that must be replaced in the
authentication phase with real Cognito JWKS verification.  The stub raises
HTTP 401 for any request that does not carry a pre-validated ``X-User-Sub``
header, which is only accepted in test/dev environments where
``AUTH_STUB_ENABLED=true`` is set.

Security controls
-----------------
- Deny by default: ``get_current_user`` raises 401 unless a valid token is
  present (OWASP A01 / A07 — Broken Access Control / Auth Failures).
- The stub path is disabled unless explicitly opted-in via env var, so it
  cannot be accidentally enabled in production (OWASP A05 — Secure Defaults).
- ``user_sub`` is the Cognito identity claim; it is never logged at INFO level
  (OWASP A09 — Security Logging).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Header, HTTPException, status


@dataclass(frozen=True)
class CognitoUser:
    """Authenticated caller identity extracted from a Cognito JWT."""

    sub: str          # Cognito ``sub`` claim — stable user identifier
    email: str = ""   # Optional; may be absent on machine accounts
    groups: tuple[str, ...] = ()


_AUTH_STUB_ENABLED: bool = (
    os.environ.get("AUTH_STUB_ENABLED", "false").lower() in {"true", "1", "yes"}
)


async def get_current_user(
    x_user_sub: str | None = Header(default=None, alias="X-User-Sub"),
) -> CognitoUser:
    """FastAPI dependency: resolve the current authenticated user.

    In production this dependency will validate a ``Bearer`` JWT against
    Cognito's JWKS endpoint.  Until that implementation is in place, it
    accepts ``X-User-Sub`` only when ``AUTH_STUB_ENABLED=true``.

    Raises:
        HTTPException 401: when the caller is not authenticated.
    """
    if _AUTH_STUB_ENABLED and x_user_sub:
        return CognitoUser(sub=x_user_sub)

    # Production path — real JWT validation (TODO: implement in auth phase)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
        headers={"WWW-Authenticate": "Bearer"},
    )

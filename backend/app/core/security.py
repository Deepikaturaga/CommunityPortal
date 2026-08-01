"""JWT creation and verification utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Return a signed JWT access token for *subject* (user UUID as string)."""
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify *token*; raises JWTError on any failure."""
    return jwt.decode(  # type: ignore[no-any-return]
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )


__all__ = ["create_access_token", "decode_access_token", "JWTError"]

"""Security utilities: password hashing, JWT creation/verification, TOTP."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

# ── Password hashing ──────────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return bcrypt hash of *plain*."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed* bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────

_TOKEN_TYPE_CLAIM = "typ"
_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    subject: str,
    *,
    extra_claims: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> str:
    """Issue a signed JWT access token for *subject* (user id / email)."""
    cfg = settings or get_settings()
    now = _now_utc()
    expire = now.timestamp() + cfg.access_token_expire_seconds
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire),
        _TOKEN_TYPE_CLAIM: _ACCESS_TOKEN_TYPE,
        "jti": secrets.token_hex(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        cfg.jwt_secret.get_secret_value(),
        algorithm=cfg.jwt_algorithm,
    )


def create_refresh_token(
    subject: str,
    *,
    settings: Settings | None = None,
) -> str:
    """Issue a signed JWT refresh token for *subject*."""
    cfg = settings or get_settings()
    now = _now_utc()
    expire = now.timestamp() + cfg.refresh_token_expire_seconds
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire),
        _TOKEN_TYPE_CLAIM: _REFRESH_TOKEN_TYPE,
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(
        payload,
        cfg.jwt_secret.get_secret_value(),
        algorithm=cfg.jwt_algorithm,
    )


def decode_access_token(
    token: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Decode and verify an access token.

    Raises
    ------
    jose.JWTError
        If the token is invalid, expired, or has the wrong type claim.
    """
    cfg = settings or get_settings()
    payload = jwt.decode(
        token,
        cfg.jwt_secret.get_secret_value(),
        algorithms=[cfg.jwt_algorithm],
    )
    if payload.get(_TOKEN_TYPE_CLAIM) != _ACCESS_TOKEN_TYPE:
        raise JWTError("Token type mismatch — expected access token")
    return payload


def decode_refresh_token(
    token: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Decode and verify a refresh token.

    Raises
    ------
    jose.JWTError
        If the token is invalid, expired, or has the wrong type claim.
    """
    cfg = settings or get_settings()
    payload = jwt.decode(
        token,
        cfg.jwt_secret.get_secret_value(),
        algorithms=[cfg.jwt_algorithm],
    )
    if payload.get(_TOKEN_TYPE_CLAIM) != _REFRESH_TOKEN_TYPE:
        raise JWTError("Token type mismatch — expected refresh token")
    return payload


# ── TOTP / MFA ────────────────────────────────────────────────────────────────


def generate_totp_secret() -> str:
    """Return a new random base-32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, *, settings: Settings | None = None) -> str:
    """Return an otpauth:// provisioning URI for authenticator apps."""
    cfg = settings or get_settings()
    totp = pyotp.TOTP(secret, digits=cfg.totp_digits, interval=cfg.totp_interval)
    return totp.provisioning_uri(name=email, issuer_name=cfg.totp_issuer)


def verify_totp(secret: str, code: str, *, settings: Settings | None = None) -> bool:
    """Return True if *code* is valid for *secret* within the allowed window."""
    cfg = settings or get_settings()
    totp = pyotp.TOTP(secret, digits=cfg.totp_digits, interval=cfg.totp_interval)
    return totp.verify(code, valid_window=cfg.totp_valid_window)


# ── CSRF token helpers ────────────────────────────────────────────────────────


def generate_csrf_token() -> str:
    """Return a cryptographically random CSRF token."""
    return secrets.token_urlsafe(32)

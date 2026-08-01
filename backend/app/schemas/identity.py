"""Pydantic schemas for the identity domain (registration / verification)."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import get_settings

# ---------------------------------------------------------------------------
_NAME_MAX = 256
_EMAIL_MAX = 254


def _password_policy(v: str) -> str:
    """Enforce password policy rules and return the validated value."""
    min_len = get_settings().password_min_length
    if len(v) < min_len:
        raise ValueError(f"Password must be at least {min_len} characters")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[^A-Za-z0-9]", v):
        raise ValueError("Password must contain at least one special character")
    return v


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """Payload for POST /api/v1/auth/register (IF-001)."""

    email: Annotated[EmailStr, Field(max_length=_EMAIL_MAX)]
    password: Annotated[str, Field(min_length=1, max_length=128)]
    full_name: Annotated[str | None, Field(default=None, max_length=_NAME_MAX)]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _password_policy(v)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        """Lower-case and strip the email address (sanitization)."""
        return v.strip().lower()

    @field_validator("full_name")
    @classmethod
    def sanitise_name(cls, v: str | None) -> str | None:
        """Strip leading/trailing whitespace from the display name."""
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class VerifyEmailRequest(BaseModel):
    """Payload for POST /api/v1/auth/verify-email."""

    token: Annotated[str, Field(min_length=1, max_length=256)]


class ResendVerificationRequest(BaseModel):
    """Payload for POST /api/v1/auth/resend-verification."""

    email: Annotated[EmailStr, Field(max_length=_EMAIL_MAX)]

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class RegisterResponse(BaseModel):
    """Successful registration response."""

    message: str
    email: str


class VerifyEmailResponse(BaseModel):
    """Successful email verification response."""

    message: str
    email: str


class ResendVerificationResponse(BaseModel):
    """Resend verification email response."""

    message: str

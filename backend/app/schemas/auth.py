"""Pydantic schemas for authentication request/response."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Request bodies ────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _password_complexity(cls, v: str) -> str:
        errors: list[str] = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if errors:
            raise ValueError("Password must contain: " + ", ".join(errors))
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    totp_code: str | None = Field(default=None, min_length=6, max_length=8)


class RefreshRequest(BaseModel):
    """Body is empty; token arrives via HttpOnly cookie."""


class TOTPSetupRequest(BaseModel):
    """Confirm TOTP enrollment by submitting the first valid code."""

    code: str = Field(min_length=6, max_length=8)


class TOTPVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# ── Response bodies ───────────────────────────────────────────────────────────


class UserOut(BaseModel):
    id: int
    email: str
    is_active: bool
    is_verified: bool
    totp_enabled: bool

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """
    Tokens are NOT returned in the body — they live in HttpOnly cookies.
    The CSRF token IS returned so the client JS can attach it to mutation headers.
    """

    message: str = "Login successful"
    csrf_token: str
    user: UserOut
    mfa_required: bool = False


class RefreshResponse(BaseModel):
    message: str = "Token refreshed"
    csrf_token: str


class TOTPSetupResponse(BaseModel):
    secret: str
    uri: str
    message: str = "Scan the QR code with your authenticator app"


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None

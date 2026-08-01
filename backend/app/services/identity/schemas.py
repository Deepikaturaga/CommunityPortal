from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """Credentials submitted by the client.

    Both fields are required; whitespace is stripped from email.
    The password length cap prevents DOS via bcrypt with very long inputs.
    """

    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)

    @model_validator(mode="after")
    def _strip_email(self) -> LoginRequest:
        # EmailStr already normalises; explicit strip for safety
        self.email = self.email.strip().lower()
        return self


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class LoginSuccess(BaseModel):
    """Returned when credentials are valid AND no MFA is configured."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int  # seconds


class MFAChallengeResponse(BaseModel):
    """Returned when credentials are valid AND MFA is required.

    The challenge_token is an opaque signed token; the client must present
    it alongside the OTP to `POST /api/v1/auth/mfa/verify`.
    """

    mfa_required: bool = True
    challenge_token: str
    mfa_method: str  # "totp" | "email_otp"
    expires_at: datetime


class LoginErrorDetail(BaseModel):
    """Generic error payload — never reveals which field was wrong."""

    code: str
    message: str


# ---------------------------------------------------------------------------
# MFA verify request
# ---------------------------------------------------------------------------


class MFAVerifyRequest(BaseModel):
    """Body for POST /api/v1/auth/mfa/verify.

    Both fields are required.  The challenge_token is the opaque signed
    string returned by /auth/login; otp_code is the digit string from
    the authenticator app (or email OTP).
    """

    challenge_token: str = Field(min_length=1, max_length=2048)
    otp_code: str = Field(
        min_length=1,
        max_length=64,
        description="TOTP digit string or email OTP.",
    )


# ---------------------------------------------------------------------------
# Internal transfer objects (not exposed in API response body)
# ---------------------------------------------------------------------------


class _UserLoginView(BaseModel):
    """Read-only projection used by the login service."""

    model_config = {"from_attributes": True}

    id: UUID
    email: str
    password_hash: str
    status: str
    mfa_method: str
    mfa_enabled: bool
    failed_login_count: int
    locked_until: datetime | None

"""User Pydantic schemas (request/response DTOs)."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    model_config = {"from_attributes": True}

    id: str
    is_active: bool
    is_verified: bool


class UserProfileUpdate(BaseModel):
    """Fields a user can update on their own profile."""

    full_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

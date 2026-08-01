"""Auth Pydantic schemas (request/response)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.auth.models import Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: Role = Role.VIEWER


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

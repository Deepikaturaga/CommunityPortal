"""Pydantic schemas for User domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    display_name: str = Field(default="", max_length=120)
    role: UserRole = UserRole.READER


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserInDB(UserRead):
    hashed_password: str

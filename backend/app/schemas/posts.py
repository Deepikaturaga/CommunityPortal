"""Pydantic schemas for Post domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import PostStatus


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    body: str = Field(default="")
    status: PostStatus = PostStatus.DRAFT


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(
        default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    body: str | None = None
    status: PostStatus | None = None


class PostRead(PostBase):
    id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

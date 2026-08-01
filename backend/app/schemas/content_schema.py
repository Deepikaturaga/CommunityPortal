"""Pydantic v2 schemas for content-item operations."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.content import ContentStatus


class ContentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    body: str = Field(default="", max_length=100_000)
    status: ContentStatus = ContentStatus.DRAFT


class ContentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    body: str | None = Field(default=None, max_length=100_000)
    status: ContentStatus | None = None


class ContentResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    body: str
    status: ContentStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

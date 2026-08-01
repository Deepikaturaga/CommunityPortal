from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KBArticleCreateRequest(BaseModel):
    title: str = Field(min_length=5, max_length=300)
    body: str = Field(min_length=10)
    summary: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)
    tags: str | None = Field(default=None, max_length=500)


class KBArticleUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=300)
    body: str | None = None
    summary: str | None = None
    category: str | None = None
    tags: str | None = None
    status: str | None = None


class KBArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    slug: str
    body: str
    summary: str | None
    author_id: int
    status: str
    category: str | None
    tags: str | None
    view_count: int
    created_at: datetime
    updated_at: datetime

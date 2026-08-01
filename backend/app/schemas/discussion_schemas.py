from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DiscussionCreateRequest(BaseModel):
    title: str = Field(min_length=5, max_length=300)
    body: str = Field(min_length=10)
    tags: str | None = Field(default=None, max_length=500)


class DiscussionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=300)
    body: str | None = None
    tags: str | None = None
    status: str | None = None


class DiscussionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    body: str
    author_id: int
    status: str
    is_pinned: bool
    view_count: int
    tags: str | None
    created_at: datetime
    updated_at: datetime


class PostCreateRequest(BaseModel):
    body: str = Field(min_length=1)
    parent_id: int | None = None


class PostUpdateRequest(BaseModel):
    body: str = Field(min_length=1)


class PostResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    body: str
    discussion_id: int
    author_id: int
    parent_id: int | None
    is_accepted_answer: bool
    is_deleted: bool
    upvote_count: int
    created_at: datetime
    updated_at: datetime

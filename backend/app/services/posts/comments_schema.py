"""Pydantic request/response schemas for comments (IF-017 contract)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CommentCreate(BaseModel):
    """Request body for POST /posts/{post_id}/comments."""

    body: str = Field(..., min_length=1, max_length=10_000, description="Comment text")

    @field_validator("body")
    @classmethod
    def strip_body(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("body must not be blank")
        return stripped


class CommentResponse(BaseModel):
    """Response envelope for a single comment."""

    id: UUID
    post_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── IF-017 event payload ──────────────────────────────────────────────────────

class CommentCreatedEvent(BaseModel):
    """
    IF-017 — event published when a comment is persisted.

    Consumers (notification service, etc.) subscribe to this shape.
    Fields are intentionally stable; add new optional fields, never remove.
    """

    event_type: str = "comment.created"
    comment_id: UUID
    post_id: UUID
    author_id: UUID  # commenter
    post_author_id: UUID  # recipient for notification
    body_preview: str = Field(
        ...,
        description="First 200 chars of the comment body — safe for notification text",
    )
    occurred_at: datetime

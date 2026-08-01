from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.models.enums import ReplyStatus

_settings = get_settings()


class ReplyCreate(BaseModel):
    """Payload for POST /discussions/{id}/replies (AC-010)."""

    body: str = Field(
        ...,
        min_length=_settings.reply_min_length,
        max_length=_settings.reply_max_length,
        description="Reply text content.",
    )

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Reply body must not be blank or whitespace only.")
        return v


class ReplyUpdate(BaseModel):
    """Payload for PATCH /discussions/{id}/replies/{reply_id} (AC-013 edit auth)."""

    body: str = Field(
        ...,
        min_length=_settings.reply_min_length,
        max_length=_settings.reply_max_length,
        description="Updated reply text content.",
    )

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Reply body must not be blank or whitespace only.")
        return v


class ReplyResponse(BaseModel):
    """Read representation of a reply."""

    model_config = {"from_attributes": True}

    id: int
    discussion_id: int
    author_id: int
    body: str
    status: ReplyStatus
    is_hidden: bool
    created_at: datetime
    updated_at: datetime

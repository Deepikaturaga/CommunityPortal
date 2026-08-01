"""Pydantic v2 schemas for the moderation review queue and actions (IF-009)."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models.content import ContentStatus
from app.models.moderation import ModerationAction

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

ReasonStr = Annotated[
    str | None,
    StringConstraints(max_length=1024),
]


class ModerationActionRequest(BaseModel):
    """Body for POST /moderation/queue/{content_id}/actions."""

    action: ModerationAction
    reason: ReasonStr = None


class QueueListParams(BaseModel):
    """Query-parameter schema for GET /moderation/queue."""

    status: ContentStatus = ContentStatus.flagged
    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=100)] = 20


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ContentSummary(BaseModel):
    """Lightweight content item returned in the queue listing."""

    model_config = {"from_attributes": True}

    id: str
    title: str
    author_id: str
    status: ContentStatus
    created_at: datetime
    updated_at: datetime


class QueuePage(BaseModel):
    """Paginated queue listing response."""

    items: list[ContentSummary]
    total: int
    page: int
    page_size: int
    pages: int


class AuditRecordOut(BaseModel):
    """Single audit record returned after a moderation action."""

    model_config = {"from_attributes": True}

    id: str
    content_id: str
    moderator_id: str
    action: ModerationAction
    reason: str | None
    previous_status: str
    new_status: str
    created_at: datetime


class ModerationActionResponse(BaseModel):
    """Envelope returned after a successful moderation action."""

    content_id: str
    new_status: ContentStatus
    audit_record: AuditRecordOut

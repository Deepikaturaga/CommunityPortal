"""
Pydantic v2 schemas for COMP-006 report intake (IF-008).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.services.moderation.models import ReportReason, ReportStatus

# ── Request ───────────────────────────────────────────────────────────────────

_UUIDStr = Annotated[str, StringConstraints(min_length=36, max_length=36)]


class ReportCreate(BaseModel):
    """Body for POST /moderation/reports (IF-008)."""

    reporter_id: _UUIDStr = Field(
        ...,
        description="UUID of the user filing the report.",
    )
    target_id: _UUIDStr = Field(
        ...,
        description="UUID of the user or content being reported.",
    )
    reason: ReportReason = Field(
        ...,
        description="Category that best describes the violation.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional free-text elaboration (max 2 000 chars).",
    )


# ── Response ──────────────────────────────────────────────────────────────────


class ReportResponse(BaseModel):
    """Serialised ModerationReport returned to callers."""

    id: str
    reporter_id: str
    target_id: str
    reason: ReportReason
    description: str | None
    status: ReportStatus
    reviewed_by: str | None
    reviewer_note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Paginated list ────────────────────────────────────────────────────────────


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    limit: int
    offset: int

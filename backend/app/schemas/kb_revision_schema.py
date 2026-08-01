"""
Pydantic schemas for KB revision history (IF-006).

Separation of concerns
----------------------
* ``KBRevisionCreate``       — internal use only (service layer); never exposed directly.
* ``KBRevisionRead``         — response DTO for the API layer.
* ``KBRevisionListResponse`` — paginated collection wrapper.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KBRevisionCreate(BaseModel):
    """Internal payload used by the service when recording a new revision."""

    article_id: int
    editor_id: int | None
    revision_number: int = Field(ge=1)
    title_snapshot: str = Field(min_length=1, max_length=500)
    content_snapshot: str = Field(min_length=1)
    change_summary: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(from_attributes=True)


class KBRevisionRead(BaseModel):
    """Public response schema — no mutable fields; snapshots are read-only."""

    id: int
    article_id: int
    editor_id: int | None
    revision_number: int
    title_snapshot: str
    content_snapshot: str
    change_summary: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KBRevisionListResponse(BaseModel):
    """Paginated list of revisions for a single article."""

    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    items: list[KBRevisionRead]

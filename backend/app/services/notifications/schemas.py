from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.services.notifications.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
)


# ── Preference schemas ────────────────────────────────────────────────────────


class PreferenceBase(BaseModel):
    channel: NotificationChannel
    category: NotificationCategory
    opted_out: bool = False


class PreferenceRead(PreferenceBase):
    """Response schema for a single preference row (IF-010)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: str
    created_at: datetime
    updated_at: datetime


class PreferencePut(BaseModel):
    """
    Request body for PUT /preferences/{channel}/{category}.

    Only opted_out is mutable; channel/category come from the URL path.
    """

    opted_out: bool


class PreferenceListResponse(BaseModel):
    """Paginated list of preferences for the authenticated user."""

    items: list[PreferenceRead]
    total: int


# ── Notification list schemas ─────────────────────────────────────────────────


class NotificationRead(BaseModel):
    """Response schema for a notification record (IF-010, COMP-008)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: str
    channel: NotificationChannel
    category: NotificationCategory
    status: NotificationStatus
    subject: str | None
    body: str
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of notifications for the authenticated user."""

    items: list[NotificationRead]
    total: int
    page: int
    page_size: int


# ── Query parameter schemas ───────────────────────────────────────────────────


class NotificationListParams(BaseModel):
    """Validated query parameters for the notification list endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    channel: NotificationChannel | None = None
    category: NotificationCategory | None = None
    status: NotificationStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

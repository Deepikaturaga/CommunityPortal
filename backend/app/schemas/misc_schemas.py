from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    recipient_id: int
    kind: str
    title: str
    body: str | None
    resource_url: str | None
    is_read: bool
    created_at: datetime


class NotificationMarkReadRequest(BaseModel):
    notification_ids: list[int]


class SearchResponse(BaseModel):
    query: str
    discussions: list[dict]
    kb_articles: list[dict]
    total: int


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    actor_id: int | None
    action: str
    resource_type: str | None
    resource_id: str | None
    detail: str | None
    created_at: datetime


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int

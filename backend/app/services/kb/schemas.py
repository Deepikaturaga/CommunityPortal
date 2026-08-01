"""Pydantic schemas for the KB approval and visibility services.

Covers AC-023.x (approve/reject) and AC-025.3 (visibility) response contracts.
IF-017 event shape is defined here as ``IF017ArticleApprovedEvent``
so it can be serialised and emitted / enqueued by the service layer.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models.kb_article import KBArticleStatus

# ---------------------------------------------------------------------------
# Shared field types
# ---------------------------------------------------------------------------
ReasonStr = Annotated[str | None, StringConstraints(max_length=2048)]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ApproveRequest(BaseModel):
    """AC-023.1 — body is optional; no required fields for approval."""


class RejectRequest(BaseModel):
    """AC-023.2 — rejection reason is strongly recommended but optional per spec."""

    reason: ReasonStr = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class KBApprovalEventOut(BaseModel):
    """Serialised KB approval audit event (IF-017 envelope)."""

    model_config = {"from_attributes": True}

    id: str
    article_id: str
    actor_id: str
    event_type: str
    previous_status: str
    new_status: str
    reason: str | None
    occurred_at: datetime


class KBArticleOut(BaseModel):
    """Response shape for a KB article (approve / reject / visibility endpoints)."""

    model_config = {"from_attributes": True}

    id: str
    author_id: str
    title: str
    body: str
    status: KBArticleStatus
    approved_by: str | None
    approved_at: datetime | None
    rejected_by: str | None
    rejected_at: datetime | None
    rejected_reason: str | None
    created_at: datetime
    updated_at: datetime


class ApproveResponse(BaseModel):
    """AC-023.1 — 200 body returned by the approve endpoint."""

    article: KBArticleOut
    event: KBApprovalEventOut


class RejectResponse(BaseModel):
    """AC-023.2 — 200 body returned by the reject endpoint."""

    article: KBArticleOut
    event: KBApprovalEventOut


# ---------------------------------------------------------------------------
# IF-017 domain event (emitted post-commit on approval; AC-023.5)
# ---------------------------------------------------------------------------


class IF017ArticleApprovedEvent(BaseModel):
    """IF-017 — ``kb.article.approved`` domain event payload.

    This is the canonical event shape that downstream consumers (notification
    service, search indexer, etc.) subscribe to.  The service layer serialises
    this and hands it to the event emitter / message broker adapter.
    """

    event_type: str = Field(default="kb.article.approved", frozen=True)
    article_id: str
    approved_by: str
    approved_at: datetime
    title: str
    author_id: str
    audit_event_id: str  # FK back to KBApprovalEvent.id for traceability

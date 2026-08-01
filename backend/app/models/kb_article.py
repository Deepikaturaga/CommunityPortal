        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        String(36),
        ForeignKey("kb_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
"""Knowledge-Base article domain model.

A KBArticle moves through a strict lifecycle enforced by ``KB_ARTICLE_TRANSITIONS``:

    draft ──► pending_review ──► approved
                              └──► draft  (moderator rejects with a note; author revises)

Only moderators/admins may approve or reject.
A rejection returns the article straight back to ``draft`` (AC-023.2).

Assumptions (AC-023.x / AC-025.x inferred from task description; see TASK-045 notes):
  AC-023.1  Approve endpoint: PUT /api/v1/kb/{article_id}/approve → 200 KBArticleOut
  AC-023.2  Only moderator or admin may approve (403 otherwise)
  AC-023.3  Only a pending_review article can be approved (422 on illegal transition)
  AC-023.4  On approval, status → approved + approved_by + approved_at set
  AC-023.5  An IF-017 ``kb.article.approved`` domain event is emitted post-commit
  AC-023.2  Reject endpoint: PUT /api/v1/kb/{article_id}/reject → 200 KBArticleOut
             On rejection, status → draft + rejected_reason (moderator note) stored;
             rejected_by / rejected_at recorded for audit trail.
  AC-025.3  GET /api/v1/kb/{article_id} → 404 for non-approved articles when caller
             is not moderator/admin.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class KBArticleStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"


# Explicit allowed-transition map (state machine).
KB_ARTICLE_TRANSITIONS: dict[KBArticleStatus, set[KBArticleStatus]] = {
    KBArticleStatus.draft: {KBArticleStatus.pending_review},
    # Reject returns the article to draft (AC-023.2); moderator note stored separately.
    KBArticleStatus.pending_review: {KBArticleStatus.approved, KBArticleStatus.draft},
    KBArticleStatus.approved: set(),  # terminal — no further transitions
}


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    author_id: Mapped[str] = mapped_column(
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[KBArticleStatus] = mapped_column(
        Enum(KBArticleStatus),
        nullable=False,
        default=KBArticleStatus.draft,
        index=True,
    )
    # Approval metadata
    approved_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Rejection metadata
    rejected_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships (lazy="raise" to prevent N+1 queries)
    approval_events: Mapped[list["KBApprovalEvent"]] = relationship(
        "KBApprovalEvent",
        back_populates="article",
        lazy="raise",
        cascade="all, delete-orphan",
    )


class KBApprovalEvent(Base):
    """Append-only audit log for KB approval / rejection actions (IF-017).

    The ``event_type`` field carries the IF-017 event name:
      - ``kb.article.approved``
      - ``kb.article.rejected``

    Immutability is enforced at the ORM level via SQLAlchemy event hooks
    (same pattern as ModerationAuditRecord).
    """

    __tablename__ = "kb_approval_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    article_id: Mapped[str] = mapped_column(
    )
    actor_id: Mapped[str] = mapped_column(
    )
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # "kb.article.approved" | "kb.article.rejected"
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    article: Mapped["KBArticle"] = relationship(
        "KBArticle", back_populates="approval_events", lazy="raise"
    )


from sqlalchemy import event as sa_event  # noqa: E402


@sa_event.listens_for(KBApprovalEvent, "before_update")
def _prevent_event_update(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        "KBApprovalEvent is immutable — UPDATE is forbidden (AC-023.x / append-only audit)"
    )


@sa_event.listens_for(KBApprovalEvent, "before_delete")
def _prevent_event_delete(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        "KBApprovalEvent is immutable — DELETE is forbidden (AC-023.x / append-only audit)"
    )

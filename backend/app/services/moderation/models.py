"""
STORE-006 — ModerationReport ORM model.

Unique constraint on (reporter_id, target_id) enforces AC-015.2: a single
reporter may not file more than one report against the same target.
"""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class ReportReason(str, enum.Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    MISINFORMATION = "misinformation"
    VIOLENCE = "violence"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"
    ACTIONED = "actioned"


class ModerationReport(Base):
    """
    STORE-006 — Moderation report submitted by a user.

    Constraints
    -----------
    * uq_moderation_report_reporter_target — prevents duplicate submissions
      from the same reporter against the same target (AC-015.2).
    """

    __tablename__ = "moderation_reports"

    __table_args__ = (
        # AC-015.2 duplicate-report unique constraint
        UniqueConstraint(
            "reporter_id",
            "target_id",
            name="uq_moderation_report_reporter_target",
        ),
        # performance index for moderator queue queries
        Index("ix_moderation_reports_status", "status"),
        Index("ix_moderation_reports_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Parties ──────────────────────────────────────────────────────────────
    # reporter_id and target_id are UUIDs referencing the user store.
    # They are stored as plain strings to remain decoupled from the user
    # service schema; a FK constraint is added when that table is in scope.
    reporter_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # ── Content ───────────────────────────────────────────────────────────────
    reason: Mapped[str] = mapped_column(
        Enum(ReportReason, name="report_reason_enum", create_constraint=True),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        Enum(ReportStatus, name="report_status_enum", create_constraint=True),
        nullable=False,
        default=ReportStatus.PENDING,
        server_default=ReportStatus.PENDING.value,
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    def __repr__(self) -> str:
        return (
            f"<ModerationReport id={self.id!r} "
            f"reporter={self.reporter_id!r} "
            f"target={self.target_id!r} "
            f"status={self.status!r}>"
        )

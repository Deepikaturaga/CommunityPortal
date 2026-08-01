        String(36),
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    action: Mapped[ModerationAction] = mapped_column(
        Enum(ModerationAction), nullable=False
"""Moderation audit record model.

The ``Content`` and ``User`` forward references are resolved at mapper
configuration time via SQLAlchemy's string-based relationship() lookup.
We add TYPE_CHECKING imports so mypy can resolve the annotations without
a circular import at runtime.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.user import User


class ModerationAction(str, enum.Enum):
    lock = "lock"
    hide = "hide"
    delete = "delete"


class ModerationAuditRecord(Base):
    __tablename__ = "moderation_audit_records"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content_id: Mapped[str] = mapped_column(
    )
    moderator_id: Mapped[str] = mapped_column(
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    content: Mapped["Content"] = relationship(
        "Content", back_populates="audit_records", lazy="raise"
    )
    moderator: Mapped["User"] = relationship(
        "User", back_populates="moderation_audit_records", lazy="raise"
    )


@event.listens_for(ModerationAuditRecord, "before_update")
def _prevent_audit_update(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        "ModerationAuditRecord is immutable — UPDATE is forbidden (AC-014.4)"
    )


@event.listens_for(ModerationAuditRecord, "before_delete")
def _prevent_audit_delete(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        "ModerationAuditRecord is immutable — DELETE is forbidden (AC-014.4)"
    )

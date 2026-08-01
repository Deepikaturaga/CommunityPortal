    ContentStatus.locked: {
        ContentStatus.active,
        ContentStatus.hidden,
        ContentStatus.deleted,
    },
    ContentStatus.hidden: {
        ContentStatus.active,
        ContentStatus.locked,
        ContentStatus.deleted,
    },
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ContentStatus(str, enum.Enum):
    active = "active"
    flagged = "flagged"
    locked = "locked"
    hidden = "hidden"
    deleted = "deleted"


CONTENT_TRANSITIONS: dict[ContentStatus, set[ContentStatus]] = {
    ContentStatus.active: {
        ContentStatus.flagged,
        ContentStatus.locked,
        ContentStatus.hidden,
        ContentStatus.deleted,
    },
    ContentStatus.flagged: {
        ContentStatus.active,
        ContentStatus.locked,
        ContentStatus.hidden,
        ContentStatus.deleted,
    },
    ContentStatus.deleted: set(),
}


class Content(Base):
    __tablename__ = "content"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    author_id: Mapped[str] = mapped_column(
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), nullable=False, default=ContentStatus.active, index=True
    )
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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
    audit_records: Mapped[list] = relationship(
        "ModerationAuditRecord",
        back_populates="content",
        lazy="raise",
        cascade="all, delete-orphan",
    )

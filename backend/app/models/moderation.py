from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.content import ContentItem


class ModerationVerdict(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"
    escalated = "escalated"


class ModerationAction(Base):
    __tablename__ = "moderation_actions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content_item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    moderator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    verdict: Mapped[ModerationVerdict] = mapped_column(
        Enum(ModerationVerdict, name="moderation_verdict"),
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # relationships
    content_item: Mapped[ContentItem] = relationship(
        "ContentItem", back_populates="moderation_actions"
    )

    def __repr__(self) -> str:
        return f"<ModerationAction id={self.id} verdict={self.verdict}>"

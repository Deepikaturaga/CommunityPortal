from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.moderation import ModerationAction


class ContentStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    removed = "removed"


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    author_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="content_status"),
        nullable=False,
        default=ContentStatus.pending,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # relationships
    moderation_actions: Mapped[list[ModerationAction]] = relationship(
        "ModerationAction", back_populates="content_item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ContentItem id={self.id} status={self.status}>"

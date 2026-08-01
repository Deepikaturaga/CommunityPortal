from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DiscussionStatus, ReplyStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Discussion(Base):
    """Top-level discussion thread."""

    __tablename__ = "discussions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[DiscussionStatus] = mapped_column(
        Enum(DiscussionStatus, name="discussionstatus"),
        nullable=False,
        default=DiscussionStatus.OPEN,
        server_default=DiscussionStatus.OPEN.value,
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    replies: Mapped[list["Reply"]] = relationship(
        "Reply", back_populates="discussion", cascade="all, delete-orphan"
    )

    @property
    def is_locked(self) -> bool:
        return self.status == DiscussionStatus.LOCKED


class Reply(Base):
    """A single reply within a discussion thread."""

    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    discussion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("discussions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReplyStatus] = mapped_column(
        Enum(ReplyStatus, name="replystatus"),
        nullable=False,
        default=ReplyStatus.VISIBLE,
        server_default=ReplyStatus.VISIBLE.value,
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    discussion: Mapped["Discussion"] = relationship("Discussion", back_populates="replies")

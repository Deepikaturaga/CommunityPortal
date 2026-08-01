from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.services.notifications.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotificationPreference(Base):
    """
    Per-user, per-channel, per-category opt-out flag (STORE-008 / COMP-008).

    Uniqueness: (user_id, channel, category).
    A row with opted_out=True means the user has disabled that combination.
    Missing row → default opted-in.
    """

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "channel", "category", name="uq_pref_user_channel_category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(
        SAEnum(NotificationChannel, name="notification_channel"), nullable=False
    )
    category: Mapped[NotificationCategory] = mapped_column(
        SAEnum(NotificationCategory, name="notification_category"), nullable=False
    )
    opted_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # ── back-reference (informational, not FK constraint to external users table) ─
    notifications: Mapped[list[Notification]] = relationship(
        "Notification", back_populates="preference", lazy="noload"
    )


class Notification(Base):
    """
    Individual notification record delivered or pending for a user (STORE-008).

    Designed append-only at the DB layer; no UPDATE/DELETE of delivered records.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    preference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notification_preferences.id", ondelete="SET NULL"),
        nullable=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        SAEnum(NotificationChannel, name="notification_channel"),
        nullable=False,
    )
    category: Mapped[NotificationCategory] = mapped_column(
        SAEnum(NotificationCategory, name="notification_category"),
        nullable=False,
    )
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, name="notification_status"),
        nullable=False,
        default=NotificationStatus.PENDING,
    )
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(String(4096), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    preference: Mapped[NotificationPreference | None] = relationship(
        "NotificationPreference", back_populates="notifications", lazy="noload"
    )

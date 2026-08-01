"""MediaAsset ORM model — tracks S3 objects (e.g., user avatars)."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssetStatus(str, enum.Enum):
    """Lifecycle of a media asset upload."""

    pending = "pending"      # Presigned URL issued; upload not yet confirmed
    confirmed = "confirmed"  # Client confirmed PUT succeeded
    deleted = "deleted"      # Soft-deleted; S3 object will be expired by lifecycle rule


class MediaAsset(Base):
    """Persisted record for every issued presigned upload slot."""

    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Logical purpose — 'avatar' is the only value defined so far; extensible.
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False, default="avatar")
    # S3 object key — deterministic, never contains PII
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    # Declared size (bytes) from the upload request — not yet verified from S3 ETag
    declared_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="assetstatus"), nullable=False, default=AssetStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User", back_populates="media_assets")  # noqa: F821

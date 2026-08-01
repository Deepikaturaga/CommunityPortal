from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AccountStatus(str, enum.Enum):
    """Lifecycle states for a user account."""

    UNVERIFIED = "unverified"  # email not yet confirmed
    ACTIVE = "active"  # normal operating state
    LOCKED = "locked"  # temporarily locked after brute-force
    SUSPENDED = "suspended"  # administratively suspended
    DEACTIVATED = "deactivated"  # soft-deleted / closed


class MFAMethod(str, enum.Enum):
    """Supported second-factor methods."""

    NONE = "none"
    TOTP = "totp"
    EMAIL_OTP = "email_otp"


class User(Base):
    """Core identity record.

    Sensitive fields (password_hash, totp_secret) are never serialised
    into response schemas.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Account lifecycle
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="accountstatus"),
        nullable=False,
        default=AccountStatus.UNVERIFIED,
        index=True,
    )

    # MFA configuration
    mfa_method: Mapped[MFAMethod] = mapped_column(
        Enum(MFAMethod, name="mfamethod"),
        nullable=False,
        default=MFAMethod.NONE,
    )
    totp_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Lockout tracking
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
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
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    login_attempts: Mapped[list["LoginAttempt"]] = relationship(
        "LoginAttempt", back_populates="user", cascade="all, delete-orphan"
    )
    mfa_challenges: Mapped[list["MFAChallenge"]] = relationship(
        "MFAChallenge", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} status={self.status}>"


class LoginAttempt(Base):
    """Append-only audit log of login events per user.

    Rows are inserted; never updated or deleted by application code.
    The DB constraint (see migration) enforces append-only at the
    database level via a trigger / check policy.
    """

    __tablename__ = "login_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Generic detail field — never store raw passwords or tokens
    detail: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="login_attempts")

    __table_args__ = (
        Index("ix_login_attempts_user_id_occurred_at", "user_id", "occurred_at"),
    )


class MFAChallenge(Base):
    """Short-lived MFA challenge token issued after valid password.

    The challenge_token is an opaque, signed identifier (not a raw OTP).
    """

    __tablename__ = "mfa_challenges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    challenge_token: Mapped[str] = mapped_column(
        String(512), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship("User", back_populates="mfa_challenges")

    __table_args__ = (
        Index("ix_mfa_challenges_user_id", "user_id"),
    )

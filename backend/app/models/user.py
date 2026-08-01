"""User ORM model."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Account state ──────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── MFA / TOTP ────────────────────────────────────────────────────────────
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Lockout ───────────────────────────────────────────────────────────────
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Refresh token family (rotation / replay detection) ───────────────────
    # Stores the JTI of the current valid refresh token.  A reuse of an
    # invalidated JTI triggers family revocation (all tokens for this user
    # are implicitly invalidated by rotating this value).
    refresh_token_jti: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def is_locked(self, now: datetime | None = None) -> bool:
        """Return True if account is currently locked out."""
        if self.locked_until is None:
            return False
        _now = now or datetime.now(tz=timezone.utc)
        # Ensure both are tz-aware for comparison
        locked = (
            self.locked_until.replace(tzinfo=timezone.utc)
            if self.locked_until.tzinfo is None
            else self.locked_until
        )
        return locked > _now

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"

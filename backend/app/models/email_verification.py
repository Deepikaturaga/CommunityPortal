"""Email-verification token model — TASK-016 / COMP-001."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, UUIDPrimaryKeyMixin

# Token string length: 48 URL-safe characters (~288 bits of entropy)
TOKEN_BYTES = 36


class EmailVerificationToken(Base, UUIDPrimaryKeyMixin):
    """Single-use, time-limited email verification token (COMP-001 / TASK-016).

    Design decisions
    ----------------
    * ``token`` stores a cryptographically random URL-safe string generated
      with :func:`secrets.token_urlsafe`.  It is never derived from user data.
    * ``consumed_at`` is set when the token is used; non-NULL means used.
    * ``expires_at`` is set by the service based on ``email_verification_token_ttl``.
      Tokens past this time return 410 Gone even if not yet consumed.
    * Issuing a new token marks previous active tokens ``superseded=True``,
      ensuring only the newest token is ever valid.
    """

    __tablename__ = "email_verification_tokens"

    token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        default=lambda: secrets.token_urlsafe(TOKEN_BYTES),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # Set True when a newer token is issued so old tokens are audit-preserved.
    superseded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    def __repr__(self) -> str:
        return (
            f"<EmailVerificationToken id={self.id} user_id={self.user_id} "
            f"consumed={self.consumed_at is not None} superseded={self.superseded}>"
        )

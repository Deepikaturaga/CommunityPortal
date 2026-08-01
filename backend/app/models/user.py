"""User domain model — STORE-001."""

from __future__ import annotations

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered user account (STORE-001).

    - ``email`` is stored lower-cased and has a unique index.
    - ``password_hash`` stores the bcrypt digest; the plain-text password is
      never persisted.
    - ``is_verified`` is False until the email-verification link is clicked
      (COMP-001 / IF-001).
    - ``is_active`` allows soft-disabling an account without deleting it.
    """

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Verification state (COMP-001)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Administrative soft-disable
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} verified={self.is_verified}>"

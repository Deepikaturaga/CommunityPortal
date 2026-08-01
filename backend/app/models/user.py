"""User ORM model (established by PHASE-022 / TASK-035)."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, enum.Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.user
    )

    # back-references populated by child models
    moderation_audit_records: Mapped[list["app.models.moderation.ModerationAuditRecord"]] = (  # type: ignore[name-defined]
        relationship("ModerationAuditRecord", back_populates="moderator", lazy="raise")
    )

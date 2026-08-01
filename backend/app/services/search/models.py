"""ORM model for searchable documents (IF-014 domain entity)."""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Visibility(str, enum.Enum):
    """Controls which roles can find a document via the search API."""

    public = "public"      # Any authenticated user
    internal = "internal"  # editor or admin only
    private = "private"    # admin only


class Document(Base):
    """Indexed document that the search service queries."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, name="visibility_enum", create_constraint=True),
        nullable=False,
        default=Visibility.public,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        # Full-text search helper index on title for ILIKE queries (Postgres)
        Index("ix_documents_title_trgm", "title"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} visibility={self.visibility}>"

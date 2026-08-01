"""SearchableRecord — canonical source-of-truth row for indexed documents.

Every indexable entity (product, article, …) should either *be* this model
or reference it via a foreign key so the reconciler has a single table to
page through.

``payload`` uses a dialect-adaptive type: JSONB on PostgreSQL (production)
and plain JSON on SQLite (tests). ``id`` is stored as String(36) so it works
on both dialects without a conditional column type.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class _JsonOrJsonb(TypeDecorator):  # type: ignore[misc]
    """Dialect-adaptive JSON: JSONB on PostgreSQL, JSON on everything else."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> object:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class SearchableRecord(Base):
    """Represents one document that should appear in the search index."""

    __tablename__ = "searchable_records"

    # Stored as VARCHAR(36) UUID string — compatible with SQLite & PostgreSQL.
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    index_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Target search index (e.g. 'products', 'articles')",
    )
    document_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Logical document type within the index",
    )
    # Serialised payload sent verbatim to the search cluster.
    payload: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        _JsonOrJsonb,
        nullable=False,
        comment="Full document body for the search index",
    )
    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Denormalised human-readable title for audit / debugging",
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="SHA-256 of canonical payload; used for change-detection",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Soft-delete flag — inactive rows are removed from the index",
    )
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

    def __repr__(self) -> str:
        return f"<SearchableRecord id={self.id} index={self.index_name}>"

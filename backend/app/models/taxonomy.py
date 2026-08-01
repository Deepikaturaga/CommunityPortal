"""Taxonomy ORM models."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TaxonomyVocabulary(Base):
    """Top-level vocabulary (e.g. 'genre', 'topic')."""

    __tablename__ = "taxonomy_vocabularies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    terms: Mapped[list["TaxonomyTerm"]] = relationship(
        "TaxonomyTerm", back_populates="vocabulary", lazy="select", cascade="all, delete-orphan"
    )


class TaxonomyTerm(Base):
    """Term belonging to a vocabulary."""

    __tablename__ = "taxonomy_terms"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    vocabulary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("taxonomy_vocabularies.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    vocabulary: Mapped["TaxonomyVocabulary"] = relationship(
        "TaxonomyVocabulary", back_populates="terms"
    )
    created_by_user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="taxonomy_terms"
    )

"""
KBRevision — append-only revision record for KB articles.

Design invariants
-----------------
* Rows are INSERT-only; UPDATE and DELETE are blocked at the ORM level via
  ``@event.listens_for`` hooks and additionally constrained in the DB trigger
  defined in the companion Alembic migration.
* ``content_snapshot`` stores the full article body at the moment of the save
  so that a complete diff can be reconstructed without joining to the live row.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    event,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base  # project's declarative base

if TYPE_CHECKING:
    from app.models.kb_article import KBArticle
    from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KBRevision(Base):
    """Immutable snapshot of a KBArticle at the moment of every save."""

    __tablename__ = "kb_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Foreign keys ─────────────────────────────────────────────────────────
    article_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("kb_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    editor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Payload ───────────────────────────────────────────────────────────────
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    content_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps (server-side default as defence-in-depth) ──────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        server_default=text("NOW()"),
    )

    # ── Relationships (read-only navigation) ─────────────────────────────────
    article: Mapped["KBArticle"] = relationship("KBArticle", back_populates="revisions")
    editor: Mapped["User | None"] = relationship("User")

    # ── Composite indexes ─────────────────────────────────────────────────────
    __table_args__ = (
        Index(
            "ix_kb_revisions_article_rev", "article_id", "revision_number", unique=True
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<KBRevision id={self.id} article_id={self.article_id} "
            f"rev={self.revision_number}>"
        )


# ── Append-only enforcement at the ORM layer ─────────────────────────────────
# These listeners fire *before* SQLAlchemy emits UPDATE/DELETE statements.
# They act as a last line of defence; the real constraint lives in the DB trigger
# created by the Alembic migration.


@event.listens_for(KBRevision, "before_update")
def _block_revision_update(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        f"KBRevision is append-only — UPDATE is forbidden (id={target.id})."
    )


@event.listens_for(KBRevision, "before_delete")
def _block_revision_delete(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        f"KBRevision is append-only — DELETE is forbidden (id={target.id})."
    )

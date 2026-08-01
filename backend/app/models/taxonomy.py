import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    pass  # forward refs for content models when added


class TaxonomyStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


# ---------------------------------------------------------------------------
# Association tables — created once and referenced by content models.
# They use plain integer FKs so they survive category/tag archival.
# ---------------------------------------------------------------------------

content_category = Table(
    "content_category",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False),
    Column(
        "category_id",
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    UniqueConstraint("content_id", "category_id", name="uq_content_category"),
)

content_tag = Table(
    "content_tag",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    UniqueConstraint("content_id", "tag_id", name="uq_content_tag"),
)


# ---------------------------------------------------------------------------
# Category — supports one level of hierarchy via nullable parent_id.
# Archiving a parent does NOT cascade-archive children; that is a UI concern.
# ---------------------------------------------------------------------------


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[TaxonomyStatus] = mapped_column(
        Enum(TaxonomyStatus, name="taxonomystatus"),
        nullable=False,
        default=TaxonomyStatus.active,
        server_default=text("'active'"),
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # self-referential relationship
    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side="Category.id", back_populates="children", lazy="selectin"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", lazy="selectin"
    )

    def archive(self) -> None:
        self.status = TaxonomyStatus.archived

    def restore(self) -> None:
        self.status = TaxonomyStatus.active

    @property
    def is_archived(self) -> bool:
        return self.status == TaxonomyStatus.archived


# ---------------------------------------------------------------------------
# Tag — flat, globally-scoped.
# ---------------------------------------------------------------------------


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[TaxonomyStatus] = mapped_column(
        Enum(TaxonomyStatus, name="taxonomystatus"),
        nullable=False,
        default=TaxonomyStatus.active,
        server_default=text("'active'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def archive(self) -> None:
        self.status = TaxonomyStatus.archived

    def restore(self) -> None:
        self.status = TaxonomyStatus.active

    @property
    def is_archived(self) -> bool:
        return self.status == TaxonomyStatus.archived

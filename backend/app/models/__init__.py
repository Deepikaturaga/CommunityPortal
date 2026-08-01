"""Central model registry — import here so Alembic autogenerate sees every table."""

from app.models.content import Content  # noqa: F401  stub FK target
from app.models.taxonomy import Category, Tag, TaxonomyStatus, content_category, content_tag  # noqa: F401

__all__ = [
    "Content",
    "Category",
    "Tag",
    "TaxonomyStatus",
    "content_category",
    "content_tag",
]

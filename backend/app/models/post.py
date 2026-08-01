"""
Post model re-exports.

The canonical storage for user posts is the ``Content`` table introduced in
PHASE-026.  The posts service (PHASE-027) builds CRUD operations on top of
that same table.  This module re-exports the relevant symbols so that the
posts service can import from a stable, domain-named location.
"""
from __future__ import annotations

from app.models.content import Content, ContentStatus, CONTENT_TRANSITIONS  # noqa: F401

# Convenience alias so that posts-service code reads naturally.
Post = Content
PostStatus = ContentStatus

__all__ = [
    "Post",
    "PostStatus",
    "Content",
    "ContentStatus",
    "CONTENT_TRANSITIONS",
]

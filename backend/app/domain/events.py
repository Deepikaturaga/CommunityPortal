from __future__ import annotations

from enum import StrEnum


class ContentEventType(StrEnum):
    """Domain event types emitted on content lifecycle changes (IF-017)."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    APPROVED = "approved"
    HIDDEN = "hidden"

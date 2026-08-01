from __future__ import annotations

import enum


class DiscussionStatus(str, enum.Enum):
    """Lifecycle status of a top-level discussion thread."""

    OPEN = "open"
    LOCKED = "locked"   # No new replies allowed (AC-012)
    HIDDEN = "hidden"   # Not surfaced in listings (AC-013)


class ReplyStatus(str, enum.Enum):
    """Visibility/moderation status of a single reply."""

    VISIBLE = "visible"
    HIDDEN = "hidden"   # Soft-hidden by moderator (AC-013)

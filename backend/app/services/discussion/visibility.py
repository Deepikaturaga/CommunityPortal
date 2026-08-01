from __future__ import annotations

"""Visibility filtering helpers for discussions and replies.

AC-012.3: Hidden discussions/replies must be excluded from non-moderator views.
AC-013.3: Moderators receive the full unfiltered set (include_hidden=True).

These are pure filter functions operating on SQLAlchemy Select statements so
they stay decoupled from HTTP concerns and are independently testable.
"""

from sqlalchemy import Select

from app.models.discussion import Discussion, Reply
from app.models.enums import DiscussionStatus, ReplyStatus


def apply_discussion_visibility(
    stmt: Select[tuple[Discussion]],
    *,
    include_hidden: bool,
) -> Select[tuple[Discussion]]:
    """Restrict a Discussion query to visible rows unless caller is a moderator.

    - Excludes rows where ``Discussion.is_hidden`` is True.
    - Excludes rows where ``Discussion.status == DiscussionStatus.HIDDEN``.

    Args:
        stmt: An existing ``select(Discussion)`` statement to filter.
        include_hidden: When True (moderator path) no filter is applied.

    Returns:
        The (possibly filtered) statement.
    """
    if include_hidden:
        return stmt
    return stmt.where(
        Discussion.is_hidden.is_(False),
        Discussion.status != DiscussionStatus.HIDDEN,
    )


def apply_reply_visibility(
    stmt: Select[tuple[Reply]],
    *,
    include_hidden: bool,
) -> Select[tuple[Reply]]:
    """Restrict a Reply query to visible rows unless caller is a moderator.

    - Excludes rows where ``Reply.is_hidden`` is True.
    - Excludes rows where ``Reply.status == ReplyStatus.HIDDEN``.

    Args:
        stmt: An existing ``select(Reply)`` statement to filter.
        include_hidden: When True (moderator path) no filter is applied.

    Returns:
        The (possibly filtered) statement.
    """
    if include_hidden:
        return stmt
    return stmt.where(
        Reply.is_hidden.is_(False),
        Reply.status == ReplyStatus.VISIBLE,
    )


def is_discussion_visible(discussion: Discussion, *, include_hidden: bool) -> bool:
    """Return True when *discussion* should be surfaced to the caller.

    Used for single-object checks after a fetch (e.g. get-by-id paths).
    """
    if include_hidden:
        return True
    return not discussion.is_hidden and discussion.status != DiscussionStatus.HIDDEN


def is_reply_visible(reply: Reply, *, include_hidden: bool) -> bool:
    """Return True when *reply* should be surfaced to the caller."""
    if include_hidden:
        return True
    return not reply.is_hidden and reply.status == ReplyStatus.VISIBLE

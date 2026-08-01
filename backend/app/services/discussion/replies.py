from __future__ import annotations

# Reply service — business rules for creating, editing, and hiding replies.
# AC-010:   Reply creation with length validation.
# AC-012:   Reject replies on locked/hidden discussions.
# AC-012.3: Hidden items excluded from non-moderator views (via visibility module).
# AC-013:   Edit authorisation — only the reply author may edit.
# AC-013.2: Non-author edit raises ReplyForbiddenError → HTTP 403.
# AC-013.3: Moderators receive unfiltered result sets (include_hidden=True).
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion, Reply
from app.models.enums import DiscussionStatus, ReplyStatus
from app.services.discussion.exceptions import (
    DiscussionHiddenError,
    DiscussionLockedError,
    DiscussionNotFoundError,
    ReplyBodyTooLongError,
    ReplyBodyTooShortError,
    ReplyForbiddenError,
    ReplyHiddenError,
    ReplyNotFoundError,
)
from app.services.discussion.visibility import (
    apply_reply_visibility,
    is_discussion_visible,
    is_reply_visible,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_discussion_or_404(
    db: AsyncSession,
    discussion_id: int,
    *,
    include_hidden: bool = True,
) -> Discussion:
    """Fetch a Discussion by PK; apply visibility filter when *include_hidden* is False.

    Raises:
        DiscussionNotFoundError: row absent.
        DiscussionHiddenError:   row is hidden and caller is not a moderator.
    """
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    discussion = result.scalar_one_or_none()
    if discussion is None:
        raise DiscussionNotFoundError(discussion_id)
    if not is_discussion_visible(discussion, include_hidden=include_hidden):
        raise DiscussionHiddenError(discussion_id)
    return discussion


async def _get_reply_or_404(
    db: AsyncSession,
    reply_id: int,
    discussion_id: int,
    *,
    include_hidden: bool = True,
) -> Reply:
    """Fetch a Reply by PK scoped to *discussion_id*; apply visibility when requested.

    Raises:
        ReplyNotFoundError: row absent or (when include_hidden=False) hidden.
    """
    result = await db.execute(
        select(Reply).where(Reply.id == reply_id, Reply.discussion_id == discussion_id)
    )
    reply = result.scalar_one_or_none()
    if reply is None:
        raise ReplyNotFoundError(reply_id)
    if not is_reply_visible(reply, include_hidden=include_hidden):
        raise ReplyNotFoundError(reply_id)
    return reply


def _assert_discussion_accepts_replies(discussion: Discussion) -> None:
    """AC-012: Raise if the discussion is locked or hidden."""
    if discussion.status == DiscussionStatus.LOCKED:
        raise DiscussionLockedError(discussion.id)
    if discussion.is_hidden or discussion.status == DiscussionStatus.HIDDEN:
        raise DiscussionHiddenError(discussion.id)


def _assert_reply_visible_for_edit(reply: Reply) -> None:
    """Prevent editing a hidden reply — service guard independent of caller role."""
    if reply.is_hidden or reply.status == ReplyStatus.HIDDEN:
        raise ReplyHiddenError(reply.id)


def _assert_is_author(reply: Reply, user_id: int) -> None:
    """AC-013.2: Raise ReplyForbiddenError (→ 403) when caller is not the reply author."""
    if reply.author_id != user_id:
        raise ReplyForbiddenError(reply.id)


def _validate_body(body: str, min_length: int, max_length: int) -> None:
    """Programmatic length guard (mirrors Pydantic schema validation for service-layer callers)."""
    stripped = body.strip()
    if len(stripped) < min_length:
        raise ReplyBodyTooShortError(min_length)
    if len(body) > max_length:
        raise ReplyBodyTooLongError(max_length)


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def create_reply(
    db: AsyncSession,
    *,
    discussion_id: int,
    author_id: int,
    body: str,
    min_length: int = 1,
    max_length: int = 10_000,
) -> Reply:
    """Create a new reply on a discussion.

    Raises:
        DiscussionNotFoundError: discussion does not exist.
        DiscussionLockedError:   discussion is locked (AC-012) → 423.
        DiscussionHiddenError:   discussion is hidden (AC-012) → 404.
        ReplyBodyTooShortError:  body is empty/blank (AC-010).
        ReplyBodyTooLongError:   body exceeds max_length (AC-010).
    """
    _validate_body(body, min_length, max_length)

    discussion = await _get_discussion_or_404(db, discussion_id)
    _assert_discussion_accepts_replies(discussion)  # AC-012

    reply = Reply(
        discussion_id=discussion_id,
        author_id=author_id,
        body=body,
        status=ReplyStatus.VISIBLE,
        is_hidden=False,
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return reply


async def update_reply(
    db: AsyncSession,
    *,
    discussion_id: int,
    reply_id: int,
    requesting_user_id: int,
    new_body: str,
    min_length: int = 1,
    max_length: int = 10_000,
) -> Reply:
    """Edit an existing reply.

    Only the reply's own author may edit (AC-013.2).  Moderator role grants
    list/read visibility but NOT edit permission on behalf of another user.

    Raises:
        DiscussionNotFoundError: parent discussion does not exist.
        DiscussionLockedError:   discussion is locked — edits blocked (AC-012) → 423.
        ReplyNotFoundError:      reply absent in this discussion.
        ReplyHiddenError:        reply is hidden — cannot edit.
        ReplyForbiddenError:     caller is not the reply author (AC-013.2) → 403.
        ReplyBodyTooShortError / ReplyBodyTooLongError: length validation (AC-010).
    """
    _validate_body(new_body, min_length, max_length)

    discussion = await _get_discussion_or_404(db, discussion_id)
    _assert_discussion_accepts_replies(discussion)  # locked threads block edits too

    # Fetch reply without visibility filter — hidden replies exist but cannot be edited
    result = await db.execute(
        select(Reply).where(Reply.id == reply_id, Reply.discussion_id == discussion_id)
    )
    reply = result.scalar_one_or_none()
    if reply is None:
        raise ReplyNotFoundError(reply_id)

    _assert_reply_visible_for_edit(reply)         # hidden → 404
    _assert_is_author(reply, requesting_user_id)  # AC-013.2: non-author → 403

    reply.body = new_body
    reply.updated_at = _utcnow()
    await db.commit()
    await db.refresh(reply)
    return reply


async def get_reply(
    db: AsyncSession,
    *,
    discussion_id: int,
    reply_id: int,
    include_hidden: bool = False,
) -> Reply:
    """Fetch a single reply.

    Args:
        include_hidden: When True (moderator) hidden replies are returned.
                        When False (default) a hidden reply raises ReplyNotFoundError.

    Raises:
        DiscussionNotFoundError: parent discussion absent.
        ReplyNotFoundError:      reply absent or hidden (when include_hidden=False).
    """
    # AC-012.3: a non-moderator must not be able to read replies on a hidden discussion.
    await _get_discussion_or_404(db, discussion_id, include_hidden=include_hidden)
    return await _get_reply_or_404(db, reply_id, discussion_id, include_hidden=include_hidden)


async def list_replies(
    db: AsyncSession,
    *,
    discussion_id: int,
    include_hidden: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Reply]:
    """Return paginated replies for a discussion.

    AC-012.3: When include_hidden=False (non-moderator) hidden replies are excluded.
    AC-013.3: When include_hidden=True (moderator)  all replies are returned.
    AC-012.3: Hidden discussion is opaque 404 for non-moderators.

    Raises:
        DiscussionNotFoundError: parent discussion absent.
        DiscussionHiddenError:   discussion is hidden and caller is not a moderator.
    """
    # AC-012.3: hidden discussion is opaque 404 for non-moderators; moderators can list freely.
    await _get_discussion_or_404(db, discussion_id, include_hidden=include_hidden)

    stmt = select(Reply).where(Reply.discussion_id == discussion_id)
    stmt = apply_reply_visibility(stmt, include_hidden=include_hidden)
    stmt = stmt.order_by(Reply.created_at.asc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())

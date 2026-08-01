from __future__ import annotations
# Unit tests for app.services.discussion.replies
# Covers: AC-010 (length), AC-012 (lock/hide rejection), AC-013 (edit auth)
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import DiscussionStatus, ReplyStatus
from app.services.discussion import replies as svc
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
from tests.conftest import make_discussion


# ─── AC-010: reply creation + length validation ────────────────────────────


@pytest.mark.asyncio
async def test_create_reply_success(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    reply = await svc.create_reply(
        db, discussion_id=discussion.id, author_id=42, body="Hello world"
    )
    assert reply.id is not None
    assert reply.body == "Hello world"
    assert reply.author_id == 42
    assert reply.status == ReplyStatus.VISIBLE
    assert reply.is_hidden is False


@pytest.mark.asyncio
async def test_create_reply_blank_body_raises(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    with pytest.raises(ReplyBodyTooShortError):
        await svc.create_reply(
            db, discussion_id=discussion.id, author_id=1, body="   ", min_length=1
        )


@pytest.mark.asyncio
async def test_create_reply_body_too_long_raises(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    with pytest.raises(ReplyBodyTooLongError):
        await svc.create_reply(
            db,
            discussion_id=discussion.id,
            author_id=1,
            body="x" * 101,
            max_length=100,
        )


@pytest.mark.asyncio
async def test_create_reply_unknown_discussion_raises(db: AsyncSession) -> None:
    with pytest.raises(DiscussionNotFoundError):
        await svc.create_reply(db, discussion_id=9999, author_id=1, body="Hi")


# ─── AC-012: lock-state rejection ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_reply_on_locked_discussion_raises(db: AsyncSession) -> None:
    """AC-012: Posting a reply to a LOCKED discussion must raise DiscussionLockedError."""
    discussion = await make_discussion(db, status=DiscussionStatus.LOCKED)
    with pytest.raises(DiscussionLockedError):
        await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="Hi")


@pytest.mark.asyncio
async def test_create_reply_on_hidden_discussion_raises(db: AsyncSession) -> None:
    """AC-012: Posting a reply to a HIDDEN discussion must raise DiscussionHiddenError."""
    discussion = await make_discussion(db, status=DiscussionStatus.HIDDEN)
    with pytest.raises(DiscussionHiddenError):
        await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="Hi")


@pytest.mark.asyncio
async def test_create_reply_on_is_hidden_discussion_raises(db: AsyncSession) -> None:
    """AC-012: is_hidden flag also blocks replies."""
    discussion = await make_discussion(db, is_hidden=True)
    with pytest.raises(DiscussionHiddenError):
        await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="Hi")


@pytest.mark.asyncio
async def test_open_discussion_accepts_replies(db: AsyncSession) -> None:
    """Sanity: OPEN discussion allows replies."""
    discussion = await make_discussion(db, status=DiscussionStatus.OPEN)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=5, body="Works")
    assert reply.id is not None


# ─── AC-012: edit on locked discussion also blocked ────────────────────────


@pytest.mark.asyncio
async def test_update_reply_on_locked_discussion_raises(db: AsyncSession) -> None:
    """Editing a reply while the discussion is locked must also be rejected."""
    discussion = await make_discussion(db)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="original")

    # Lock the discussion
    discussion.status = DiscussionStatus.LOCKED
    await db.commit()

    with pytest.raises(DiscussionLockedError):
        await svc.update_reply(
            db,
            discussion_id=discussion.id,
            reply_id=reply.id,
            requesting_user_id=1,
            new_body="edited",
        )


# ─── AC-013: edit authorisation ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_reply_by_author_succeeds(db: AsyncSession) -> None:
    """AC-013: The reply author can edit their own reply."""
    discussion = await make_discussion(db)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=7, body="v1")

    updated = await svc.update_reply(
        db,
        discussion_id=discussion.id,
        reply_id=reply.id,
        requesting_user_id=7,
        new_body="v2",
    )
    assert updated.body == "v2"


@pytest.mark.asyncio
async def test_update_reply_by_non_author_raises_forbidden(db: AsyncSession) -> None:
    """AC-013: A user who is NOT the author receives 403/ReplyForbiddenError."""
    discussion = await make_discussion(db)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=7, body="v1")

    with pytest.raises(ReplyForbiddenError):
        await svc.update_reply(
            db,
            discussion_id=discussion.id,
            reply_id=reply.id,
            requesting_user_id=99,  # different user
            new_body="attempted hijack",
        )


@pytest.mark.asyncio
async def test_update_hidden_reply_raises(db: AsyncSession) -> None:
    """Editing a hidden reply is rejected."""

    discussion = await make_discussion(db)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="v1")

    # Hide the reply
    reply.status = ReplyStatus.HIDDEN
    reply.is_hidden = True
    await db.commit()

    with pytest.raises(ReplyHiddenError):
        await svc.update_reply(
            db,
            discussion_id=discussion.id,
            reply_id=reply.id,
            requesting_user_id=1,
            new_body="edit attempt",
        )


@pytest.mark.asyncio
async def test_update_reply_not_found_raises(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    with pytest.raises(ReplyNotFoundError):
        await svc.update_reply(
            db,
            discussion_id=discussion.id,
            reply_id=9999,
            requesting_user_id=1,
            new_body="nope",
        )


# ─── list / get helpers ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_replies_excludes_hidden(db: AsyncSession) -> None:

    discussion = await make_discussion(db)
    r1 = await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="visible")
    r2 = await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="hidden")

    r2.status = ReplyStatus.HIDDEN
    r2.is_hidden = True
    await db.commit()

    results = await svc.list_replies(db, discussion_id=discussion.id)
    ids = [r.id for r in results]
    assert r1.id in ids
    assert r2.id not in ids


@pytest.mark.asyncio
async def test_list_replies_pagination(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    for i in range(5):
        await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body=f"reply {i}")

    page1 = await svc.list_replies(db, discussion_id=discussion.id, limit=3, offset=0)
    page2 = await svc.list_replies(db, discussion_id=discussion.id, limit=3, offset=3)
    assert len(page1) == 3
    assert len(page2) == 2

from __future__ import annotations

"""Unit tests for app.services.discussion.visibility.

Covers:
    AC-012.3 — hidden discussions/replies excluded from non-moderator views.
    AC-013.3 — moderator receives unfiltered sets (include_hidden=True).
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion, Reply
from app.models.enums import DiscussionStatus, ReplyStatus
from app.services.discussion.visibility import (
    apply_discussion_visibility,
    apply_reply_visibility,
    is_discussion_visible,
    is_reply_visible,
)
from tests.conftest import make_discussion, make_reply


# ─── is_discussion_visible ─────────────────────────────────────────────────


def _open_discussion() -> Discussion:
    d = Discussion(
        id=1, title="t", body="b", author_id=1,
        status=DiscussionStatus.OPEN, is_hidden=False,
    )
    return d


def _hidden_status_discussion() -> Discussion:
    d = Discussion(
        id=2, title="t", body="b", author_id=1,
        status=DiscussionStatus.HIDDEN, is_hidden=False,
    )
    return d


def _hidden_flag_discussion() -> Discussion:
    d = Discussion(
        id=3, title="t", body="b", author_id=1,
        status=DiscussionStatus.OPEN, is_hidden=True,
    )
    return d


class TestIsDiscussionVisible:
    def test_open_visible_to_non_moderator(self) -> None:
        assert is_discussion_visible(_open_discussion(), include_hidden=False) is True

    def test_open_visible_to_moderator(self) -> None:
        assert is_discussion_visible(_open_discussion(), include_hidden=True) is True

    def test_hidden_status_invisible_to_non_moderator(self) -> None:
        # AC-012.3
        assert is_discussion_visible(_hidden_status_discussion(), include_hidden=False) is False

    def test_hidden_status_visible_to_moderator(self) -> None:
        # AC-013.3
        assert is_discussion_visible(_hidden_status_discussion(), include_hidden=True) is True

    def test_is_hidden_flag_invisible_to_non_moderator(self) -> None:
        # AC-012.3
        assert is_discussion_visible(_hidden_flag_discussion(), include_hidden=False) is False

    def test_is_hidden_flag_visible_to_moderator(self) -> None:
        # AC-013.3
        assert is_discussion_visible(_hidden_flag_discussion(), include_hidden=True) is True


# ─── is_reply_visible ──────────────────────────────────────────────────────


def _visible_reply() -> Reply:
    return Reply(
        id=1, discussion_id=1, author_id=1, body="x",
        status=ReplyStatus.VISIBLE, is_hidden=False,
    )


def _hidden_status_reply() -> Reply:
    return Reply(
        id=2, discussion_id=1, author_id=1, body="x",
        status=ReplyStatus.HIDDEN, is_hidden=False,
    )


def _hidden_flag_reply() -> Reply:
    return Reply(
        id=3, discussion_id=1, author_id=1, body="x",
        status=ReplyStatus.VISIBLE, is_hidden=True,
    )


class TestIsReplyVisible:
    def test_visible_reply_accessible_to_non_moderator(self) -> None:
        assert is_reply_visible(_visible_reply(), include_hidden=False) is True

    def test_hidden_status_reply_inaccessible_to_non_moderator(self) -> None:
        # AC-012.3
        assert is_reply_visible(_hidden_status_reply(), include_hidden=False) is False

    def test_hidden_status_reply_accessible_to_moderator(self) -> None:
        # AC-013.3
        assert is_reply_visible(_hidden_status_reply(), include_hidden=True) is True

    def test_hidden_flag_reply_inaccessible_to_non_moderator(self) -> None:
        # AC-012.3
        assert is_reply_visible(_hidden_flag_reply(), include_hidden=False) is False

    def test_hidden_flag_reply_accessible_to_moderator(self) -> None:
        # AC-013.3
        assert is_reply_visible(_hidden_flag_reply(), include_hidden=True) is True


# ─── apply_discussion_visibility (DB query filter) ─────────────────────────


@pytest.mark.asyncio
async def test_apply_discussion_visibility_excludes_hidden_status(db: AsyncSession) -> None:
    """AC-012.3: HIDDEN-status discussions absent from non-moderator query."""
    open_d = await make_discussion(db, status=DiscussionStatus.OPEN)
    hidden_d = await make_discussion(db, status=DiscussionStatus.HIDDEN)

    stmt = apply_discussion_visibility(select(Discussion), include_hidden=False)
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert open_d.id in ids
    assert hidden_d.id not in ids


@pytest.mark.asyncio
async def test_apply_discussion_visibility_excludes_is_hidden_flag(db: AsyncSession) -> None:
    """AC-012.3: is_hidden=True discussions absent from non-moderator query."""
    visible_d = await make_discussion(db, is_hidden=False)
    hidden_d = await make_discussion(db, is_hidden=True)

    stmt = apply_discussion_visibility(select(Discussion), include_hidden=False)
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert visible_d.id in ids
    assert hidden_d.id not in ids


@pytest.mark.asyncio
async def test_apply_discussion_visibility_includes_hidden_for_moderator(
    db: AsyncSession,
) -> None:
    """AC-013.3: Moderator query returns hidden discussions too."""
    open_d = await make_discussion(db, status=DiscussionStatus.OPEN)
    hidden_d = await make_discussion(db, status=DiscussionStatus.HIDDEN)
    flag_d = await make_discussion(db, is_hidden=True)

    stmt = apply_discussion_visibility(select(Discussion), include_hidden=True)
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert open_d.id in ids
    assert hidden_d.id in ids
    assert flag_d.id in ids


# ─── apply_reply_visibility (DB query filter) ──────────────────────────────


@pytest.mark.asyncio
async def test_apply_reply_visibility_excludes_hidden(db: AsyncSession) -> None:
    """AC-012.3: hidden replies absent from non-moderator list."""
    discussion = await make_discussion(db)
    visible_r = await make_reply(db, discussion)
    hidden_r = await make_reply(db, discussion, status=ReplyStatus.HIDDEN, is_hidden=True)

    stmt = apply_reply_visibility(
        select(Reply).where(Reply.discussion_id == discussion.id),
        include_hidden=False,
    )
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert visible_r.id in ids
    assert hidden_r.id not in ids


@pytest.mark.asyncio
async def test_apply_reply_visibility_includes_hidden_for_moderator(db: AsyncSession) -> None:
    """AC-013.3: Moderator list includes hidden replies."""
    discussion = await make_discussion(db)
    visible_r = await make_reply(db, discussion)
    hidden_r = await make_reply(db, discussion, status=ReplyStatus.HIDDEN, is_hidden=True)

    stmt = apply_reply_visibility(
        select(Reply).where(Reply.discussion_id == discussion.id),
        include_hidden=True,
    )
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert visible_r.id in ids
    assert hidden_r.id in ids

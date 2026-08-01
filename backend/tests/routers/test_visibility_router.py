from __future__ import annotations

"""HTTP integration tests for hide-state filtering and edit authorisation.

Covers:
    AC-010.2 / VER-002 — locked thread → 423 Locked
    AC-012.3           — hidden replies excluded from non-moderator list/get
    AC-013.2           — non-author edit → 403 Forbidden
    AC-013.3           — moderator sees hidden replies in list and get

All tests that create their own AsyncClient (instead of using the `client`
fixture) must declare `setup_db` as a parameter so pytest-asyncio runs the
DB setup fixture before the test body.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.enums import DiscussionStatus, ReplyStatus
from tests.conftest import _make_app, _test_session_factory, make_discussion, make_reply


# ─── AC-010.2 / VER-002 ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reply_to_locked_thread_returns_423(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """VER-002: Posting a reply to a locked discussion must return 423 Locked."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db, status=DiscussionStatus.LOCKED)

    app = _make_app(user_id=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/discussions/{discussion.id}/replies",
            json={"body": "Trying to reply to locked thread"},
        )

    assert resp.status_code == 423, resp.text
    assert "locked" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_edit_reply_on_locked_thread_returns_423(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """VER-002: Editing a reply while discussion is locked must also return 423."""
    async with _test_session_factory() as db:
        open_discussion = await make_discussion(db, status=DiscussionStatus.OPEN)
        reply = await make_reply(db, open_discussion, author_id=1)
        open_discussion.status = DiscussionStatus.LOCKED
        await db.commit()

    app = _make_app(user_id=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/discussions/{open_discussion.id}/replies/{reply.id}",
            json={"body": "edit after lock"},
        )

    assert resp.status_code == 423, resp.text


# ─── AC-012.3: hidden replies excluded from non-moderator views ────────────


@pytest.mark.asyncio
async def test_list_replies_excludes_hidden_for_regular_user(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-012.3: Regular user does not see hidden replies in list endpoint."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        visible_r = await make_reply(db, discussion, body="visible reply")
        hidden_r = await make_reply(
            db, discussion, body="hidden reply",
            status=ReplyStatus.HIDDEN, is_hidden=True,
        )

    app = _make_app(user_id=1, is_moderator=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies")

    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert visible_r.id in ids
    assert hidden_r.id not in ids


@pytest.mark.asyncio
async def test_get_hidden_reply_returns_404_for_regular_user(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-012.3: GET on a hidden reply returns 404 for non-moderators."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        hidden_r = await make_reply(
            db, discussion, body="hidden",
            status=ReplyStatus.HIDDEN, is_hidden=True,
        )

    app = _make_app(user_id=1, is_moderator=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/discussions/{discussion.id}/replies/{hidden_r.id}"
        )

    assert resp.status_code == 404, resp.text


# ─── AC-013.2: non-author edit → 403 ──────────────────────────────────────


@pytest.mark.asyncio
async def test_edit_reply_by_non_author_returns_403(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.2: A user who is not the reply author receives 403 Forbidden."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        reply = await make_reply(db, discussion, author_id=1)

    app_user2 = _make_app(user_id=2)
    async with AsyncClient(
        transport=ASGITransport(app=app_user2), base_url="http://test"
    ) as client:
        resp = await client.patch(
            f"/api/v1/discussions/{discussion.id}/replies/{reply.id}",
            json={"body": "attempted hijack"},
        )

    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_edit_reply_by_author_returns_200(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.2 sanity: The reply author can edit successfully."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        reply = await make_reply(db, discussion, author_id=7)

    app_owner = _make_app(user_id=7)
    async with AsyncClient(
        transport=ASGITransport(app=app_owner), base_url="http://test"
    ) as client:
        resp = await client.patch(
            f"/api/v1/discussions/{discussion.id}/replies/{reply.id}",
            json={"body": "edited by owner"},
        )

    assert resp.status_code == 200
    assert resp.json()["body"] == "edited by owner"


@pytest.mark.asyncio
async def test_moderator_cannot_edit_on_behalf_of_another_user(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.2: Moderator role grants visibility only — not edit on another's reply."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        reply = await make_reply(db, discussion, author_id=1)

    # Moderator is user 99 (different from author 1)
    app_mod = _make_app(user_id=99, is_moderator=True)
    async with AsyncClient(
        transport=ASGITransport(app=app_mod), base_url="http://test"
    ) as client:
        resp = await client.patch(
            f"/api/v1/discussions/{discussion.id}/replies/{reply.id}",
            json={"body": "moderator override"},
        )

    assert resp.status_code == 403, resp.text


# ─── AC-013.3: moderator receives hidden items ─────────────────────────────


@pytest.mark.asyncio
async def test_list_replies_includes_hidden_for_moderator(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.3: Moderator sees hidden replies in list endpoint."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        visible_r = await make_reply(db, discussion, body="visible")
        hidden_r = await make_reply(
            db, discussion, body="hidden",
            status=ReplyStatus.HIDDEN, is_hidden=True,
        )

    app_mod = _make_app(user_id=1, is_moderator=True)
    async with AsyncClient(
        transport=ASGITransport(app=app_mod), base_url="http://test"
    ) as client:
        resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies")

    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert visible_r.id in ids
    assert hidden_r.id in ids


@pytest.mark.asyncio
async def test_get_hidden_reply_returns_200_for_moderator(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.3: Moderator can fetch a hidden reply by ID."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        hidden_r = await make_reply(
            db, discussion, body="hidden content",
            status=ReplyStatus.HIDDEN, is_hidden=True,
        )

    app_mod = _make_app(user_id=1, is_moderator=True)
    async with AsyncClient(
        transport=ASGITransport(app=app_mod), base_url="http://test"
    ) as client:
        resp = await client.get(
            f"/api/v1/discussions/{discussion.id}/replies/{hidden_r.id}"
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["body"] == "hidden content"
    assert resp.json()["is_hidden"] is True


@pytest.mark.asyncio
async def test_hidden_discussion_returns_404_for_non_moderator(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-012.3: Hidden discussion is opaque 404 for regular users."""
    async with _test_session_factory() as db:
        hidden_d = await make_discussion(db, status=DiscussionStatus.HIDDEN)

    app = _make_app(user_id=1, is_moderator=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/v1/discussions/{hidden_d.id}/replies")

    assert resp.status_code == 404, resp.text
    assert "hidden" not in resp.json()["detail"].lower()

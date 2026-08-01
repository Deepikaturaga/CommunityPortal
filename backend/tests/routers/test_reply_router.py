from __future__ import annotations

# HTTP integration tests for the reply router.
# AC-010 (creation/length), AC-010.2/VER-002 (lock-state 423), AC-012 (hidden-state 404),
# AC-013 (edit auth 403)
# Uses HTTPX ASGITransport + SQLite in-memory DB via conftest overrides.

import pytest
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.discussion import Discussion
from app.models.enums import DiscussionStatus
from tests.conftest import _make_app, _test_session_factory, make_discussion


# ─── POST /api/v1/discussions/{id}/replies ─────────────────────────────────


@pytest.mark.asyncio
async def test_create_reply_returns_201(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "Great post!"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "Great post!"
    assert data["author_id"] == 1  # default fixture user
    assert data["status"] == "visible"
    assert data["is_hidden"] is False


@pytest.mark.asyncio
async def test_create_reply_blank_body_returns_422(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "   "},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_reply_unknown_discussion_returns_404(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/discussions/9999/replies", json={"body": "Hi"})
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.user_id(1)
async def test_create_reply_locked_discussion_returns_423(client: AsyncClient) -> None:
    # AC-010.2 / VER-002: Locked discussion → 423 Locked
    async with _test_session_factory() as db:
        discussion = await make_discussion(db, status=DiscussionStatus.LOCKED)

    resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "Trying to reply"},
    )
    assert resp.status_code == 423
    assert "locked" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_reply_hidden_discussion_returns_404(client: AsyncClient) -> None:
    # AC-012: Hidden discussion → opaque 404 (must not disclose hidden status)
    async with _test_session_factory() as db:
        discussion = await make_discussion(db, status=DiscussionStatus.HIDDEN)

    resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "Trying to reply"},
    )
    assert resp.status_code == 404
    assert "hidden" not in resp.json()["detail"].lower()


# ─── PATCH /api/v1/discussions/{id}/replies/{reply_id} ─────────────────────


@pytest.mark.asyncio
async def test_update_reply_by_owner_returns_200(client: AsyncClient) -> None:
    # AC-013: Reply author can edit their own reply
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    create_resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "original"},
    )
    reply_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/discussions/{discussion.id}/replies/{reply_id}",
        json={"body": "edited"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["body"] == "edited"


@pytest.mark.asyncio
async def test_update_reply_by_non_owner_returns_403(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    # AC-013: Non-author receives 403 Forbidden
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    app_user1 = _make_app(user_id=1)
    async with AsyncClient(transport=ASGITransport(app=app_user1), base_url="http://test") as c1:
        create_resp = await c1.post(
            f"/api/v1/discussions/{discussion.id}/replies",
            json={"body": "owner reply"},
        )
    reply_id = create_resp.json()["id"]

    app_user2 = _make_app(user_id=2)
    async with AsyncClient(transport=ASGITransport(app=app_user2), base_url="http://test") as c2:
        patch_resp = await c2.patch(
            f"/api/v1/discussions/{discussion.id}/replies/{reply_id}",
            json={"body": "hijack"},
        )
    assert patch_resp.status_code == 403


@pytest.mark.asyncio
async def test_update_reply_on_locked_discussion_returns_423(client: AsyncClient) -> None:
    # AC-010.2 / VER-002: Editing a reply when discussion becomes locked → 423
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
    discussion_id = discussion.id

    create_resp = await client.post(
        f"/api/v1/discussions/{discussion_id}/replies",
        json={"body": "original"},
    )
    reply_id = create_resp.json()["id"]

    async with _test_session_factory() as db:
        result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
        d = result.scalar_one()
        d.status = DiscussionStatus.LOCKED
        await db.commit()

    patch_resp = await client.patch(
        f"/api/v1/discussions/{discussion_id}/replies/{reply_id}",
        json={"body": "edit after lock"},
    )
    assert patch_resp.status_code == 423


# ─── GET replies ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_replies_returns_200(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    await client.post(f"/api/v1/discussions/{discussion.id}/replies", json={"body": "reply 1"})
    await client.post(f"/api/v1/discussions/{discussion.id}/replies", json={"body": "reply 2"})

    resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_single_reply_returns_200(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    create_resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies", json={"body": "solo"}
    )
    reply_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies/{reply_id}")
    assert resp.status_code == 200
    assert resp.json()["body"] == "solo"


@pytest.mark.asyncio
async def test_get_nonexistent_reply_returns_404(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies/9999")
    assert resp.status_code == 404

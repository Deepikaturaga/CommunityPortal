"""
AC-021.x — Comment create endpoint + IF-017 event tests.

Coverage:
  AC-021.1  Comment persisted in DB with correct fields
  AC-021.2  HTTP 201 + CommentResponse body returned
  AC-021.3  IF-017 event emitted with correct shape
  AC-021.4  event_type == "comment.created"
  AC-021.5  post_author_id in event matches the post's author
  AC-021.6  body_preview capped at 200 chars
  AC-021.7  401 when no auth token supplied
  AC-021.8  404 when post does not exist
  AC-021.9  422 when body is blank / missing
  AC-021.10 422 when body exceeds max length
"""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.publisher import MemoryEventPublisher
from app.services.posts.models import Post
from tests.conftest import make_token

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _seed_post(session: AsyncSession, author_id: uuid.UUID | None = None) -> Post:
    """Insert a Post row directly so comment tests have a parent."""
    post = Post(
        id=uuid.uuid4(),
        author_id=author_id or uuid.uuid4(),
        title="Test Post",
        body="Post body",
    )
    async with session.begin():
        session.add(post)
    await session.refresh(post)
    return post


# ── AC-021.1 / AC-021.2 ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_comment_persisted_and_201(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.1 Comment persisted; AC-021.2 HTTP 201 + response body."""
    commenter_id = uuid.uuid4()
    post = await _seed_post(db_session)
    token = make_token(commenter_id)

    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": "Great post!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["body"] == "Great post!"
    assert data["post_id"] == str(post.id)
    assert data["author_id"] == str(commenter_id)
    assert "id" in data
    assert "created_at" in data


# ── AC-021.3 / AC-021.4 / AC-021.5 ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_if017_event_emitted(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.3 event emitted; AC-021.4 event_type; AC-021.5 post_author_id."""
    post_author_id = uuid.uuid4()
    commenter_id = uuid.uuid4()
    post = await _seed_post(db_session, author_id=post_author_id)
    token = make_token(commenter_id)

    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": "Nice work!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    assert len(memory_publisher.events) == 1
    evt = memory_publisher.events[0]
    assert evt["event_type"] == "comment.created"
    assert evt["post_id"] == str(post.id)
    assert evt["author_id"] == str(commenter_id)
    assert evt["post_author_id"] == str(post_author_id)


# ── AC-021.6 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_body_preview_capped_at_200(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.6 body_preview must not exceed 200 chars."""
    post = await _seed_post(db_session)
    long_body = "x" * 500
    token = make_token()

    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": long_body},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert len(memory_publisher.events) == 1
    preview = memory_publisher.events[0]["body_preview"]
    assert len(preview) <= 200


# ── AC-021.7 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.7 missing auth → 401."""
    post = await _seed_post(db_session)
    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": "Sneaky"},
    )
    assert resp.status_code == 401
    assert len(memory_publisher.events) == 0


# ── AC-021.8 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_not_found_returns_404(
    client: AsyncClient,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.8 non-existent post → 404; no event fired."""
    token = make_token()
    missing_id = uuid.uuid4()

    resp = await client.post(
        f"/v1/posts/{missing_id}/comments",
        json={"body": "Hello?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
    assert len(memory_publisher.events) == 0


# ── AC-021.9 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_blank_body_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.9 blank/whitespace-only body → 422."""
    post = await _seed_post(db_session)
    token = make_token()

    for bad_body in ["", "   ", "\t\n"]:
        resp = await client.post(
            f"/v1/posts/{post.id}/comments",
            json={"body": bad_body},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422, f"Expected 422 for body={bad_body!r}"

    assert len(memory_publisher.events) == 0


# ── AC-021.10 ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_oversized_body_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.10 body > 10 000 chars → 422."""
    post = await _seed_post(db_session)
    token = make_token()

    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": "a" * 10_001},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    assert len(memory_publisher.events) == 0

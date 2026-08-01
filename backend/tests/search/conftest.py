"""Shared fixtures and helpers for the search validation suite.

Extends the root tests/conftest.py with a rich seed dataset covering every
ContentStatus variant, two regular users, a moderator, and cross-ownership
combinations needed by AC-027.1–.5.

Environment bootstrap
---------------------
We set the minimum required env vars here (before any ``app.*`` import)
so this test package is self-contained when run via the search workspace.
"""
from __future__ import annotations

import os

# Bootstrap env vars before app.core.config is imported.
# These mirror the values in the reference backend's .env file.
_ENV_DEFAULTS = {
    "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "ENVIRONMENT": "test",
}
for _k, _v in _ENV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User, UserRole
from tests.conftest import make_moderator_token, make_user_token

# Re-export root conftest fixtures so pytest collects them for this package.
from tests.conftest import (  # noqa: F401
    create_test_tables,
    db_session,
    client,
    moderator_user,
    regular_user,
    flagged_content,
    active_content,
)


# ---------------------------------------------------------------------------
# Header helpers (re-exported for convenience)
# ---------------------------------------------------------------------------


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def user_auth_headers(user: User) -> dict[str, str]:
    return auth_headers(make_user_token(user))


def mod_auth_headers(user: User) -> dict[str, str]:
    return auth_headers(make_moderator_token(user))


# ---------------------------------------------------------------------------
# Seed users
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def searcher(db_session: AsyncSession) -> User:
    """Regular user who performs the search queries."""
    user = User(
        username="searcher",
        email="searcher@example.com",
        hashed_password="hashed",
        role=UserRole.user,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def author(db_session: AsyncSession) -> User:
    """Regular user who owns the seed content."""
    user = User(
        username="author",
        email="author@example.com",
        hashed_password="hashed",
        role=UserRole.user,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def search_moderator(db_session: AsyncSession) -> User:
    """Moderator used for privileged search assertions."""
    user = User(
        username="search_mod",
        email="searchmod@example.com",
        hashed_password="hashed",
        role=UserRole.moderator,
    )
    db_session.add(user)
    await db_session.flush()
    return user


# ---------------------------------------------------------------------------
# Seed content – one post per status, all owned by `author`
# ---------------------------------------------------------------------------


async def _make_post(
    db: AsyncSession,
    *,
    owner: User,
    title: str,
    body: str,
    status: ContentStatus,
    is_locked: bool = False,
) -> Content:
    post = Content(
        author_id=owner.id,
        title=title,
        body=body,
        status=status,
        is_locked=is_locked,
    )
    db.add(post)
    await db.flush()
    return post


@pytest_asyncio.fixture()
async def seed_active(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Visible active post",
        body="Regular content everyone can see.",
        status=ContentStatus.active,
    )


@pytest_asyncio.fixture()
async def seed_flagged(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Flagged unapproved post",
        body="Awaiting moderation review.",
        status=ContentStatus.flagged,
    )


@pytest_asyncio.fixture()
async def seed_hidden(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Hidden post",
        body="Removed from public view.",
        status=ContentStatus.hidden,
    )


@pytest_asyncio.fixture()
async def seed_locked(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Locked post",
        body="Comments disabled.",
        status=ContentStatus.locked,
        is_locked=True,
    )


@pytest_asyncio.fixture()
async def seed_deleted(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Soft-deleted post",
        body="Permanently removed.",
        status=ContentStatus.deleted,
    )


@pytest_asyncio.fixture()
async def full_seed(
    seed_active: Content,
    seed_flagged: Content,
    seed_hidden: Content,
    seed_locked: Content,
    seed_deleted: Content,
) -> dict[str, Content]:
    """Convenience mapping: status value → Content row."""
    return {
        "active": seed_active,
        "flagged": seed_flagged,
        "hidden": seed_hidden,
        "locked": seed_locked,
        "deleted": seed_deleted,
    }

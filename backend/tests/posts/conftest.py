"""Shared fixtures for the posts test suite.

Extends the root conftest (tests/conftest.py) with posts-specific helpers.
All fixtures here are scoped to the function level to guarantee test isolation.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.conftest import make_moderator_token, make_user_token  # re-export helpers


# ---------------------------------------------------------------------------
# Token / header helpers
# ---------------------------------------------------------------------------


def auth_headers(token: str) -> dict[str, str]:
    """Return ``Authorization: Bearer <token>`` header dict."""
    return {"Authorization": f"Bearer {token}"}


def user_auth_headers(user: User) -> dict[str, str]:
    return auth_headers(make_user_token(user))


def mod_auth_headers(user: User) -> dict[str, str]:
    return auth_headers(make_moderator_token(user))


# ---------------------------------------------------------------------------
# Post fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def active_post(db_session: AsyncSession, regular_user: User) -> Content:
    """A fresh active post owned by *regular_user*."""
    post = Content(
        author_id=regular_user.id,
        title="Hello world",
        body="This is the body.",
        status=ContentStatus.active,
        is_locked=False,
    )
    db_session.add(post)
    await db_session.flush()
    return post


@pytest_asyncio.fixture()
async def flagged_post(db_session: AsyncSession, regular_user: User) -> Content:
    """A flagged post owned by *regular_user*."""
    post = Content(
        author_id=regular_user.id,
        title="Flagged post",
        body="Reported content.",
        status=ContentStatus.flagged,
        is_locked=False,
    )
    db_session.add(post)
    await db_session.flush()
    return post


@pytest_asyncio.fixture()
async def locked_post(db_session: AsyncSession, regular_user: User) -> Content:
    """A locked post owned by *regular_user*."""
    post = Content(
        author_id=regular_user.id,
        title="Locked post",
        body="Locked content.",
        status=ContentStatus.locked,
        is_locked=True,
    )
    db_session.add(post)
    await db_session.flush()
    return post


@pytest_asyncio.fixture()
async def deleted_post(db_session: AsyncSession, regular_user: User) -> Content:
    """A soft-deleted post owned by *regular_user*."""
    post = Content(
        author_id=regular_user.id,
        title="Deleted post",
        body="Removed content.",
        status=ContentStatus.deleted,
        is_locked=False,
    )
    db_session.add(post)
    await db_session.flush()
    return post


@pytest_asyncio.fixture()
async def other_user(db_session: AsyncSession) -> User:
    """A second regular user with no posts."""
    from app.models.user import UserRole

    user = User(
        username="other_user",
        email="other@example.com",
        hashed_password="hashed",
        role=UserRole.user,
    )
    db_session.add(user)
    await db_session.flush()
    return user

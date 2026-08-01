"""Shared pytest fixtures for the moderation service tests."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.content import Content, ContentStatus
from app.models.user import User, UserRole

# ---------------------------------------------------------------------------
# In-memory SQLite engine (isolated per test session)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=test_engine, expire_on_commit=False, autoflush=False, autocommit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    """Yield a transactional session that is rolled back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncClient:
    """HTTPX async client wired to the FastAPI app with the test DB session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper fixtures: users + content
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def moderator_user(db_session: AsyncSession) -> User:
    user = User(
        username="mod1",
        email="mod1@example.com",
        hashed_password="hashed",
        role=UserRole.moderator,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def regular_user(db_session: AsyncSession) -> User:
    user = User(
        username="user1",
        email="user1@example.com",
        hashed_password="hashed",
        role=UserRole.user,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def flagged_content(db_session: AsyncSession, regular_user: User) -> Content:
    content = Content(
        author_id=regular_user.id,
        title="Flagged post",
        body="This post was flagged.",
        status=ContentStatus.flagged,
    )
    db_session.add(content)
    await db_session.flush()
    return content


@pytest_asyncio.fixture()
async def active_content(db_session: AsyncSession, regular_user: User) -> Content:
    content = Content(
        author_id=regular_user.id,
        title="Active post",
        body="This post is active.",
        status=ContentStatus.active,
    )
    db_session.add(content)
    await db_session.flush()
    return content


def make_moderator_token(user: User) -> str:
    return create_access_token(user_id=user.id, role="moderator")


def make_user_token(user: User) -> str:
    return create_access_token(user_id=user.id, role="user")

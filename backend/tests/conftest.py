"""
Shared pytest fixtures for the E2E test suite.

Every test gets:
  - a fresh in-memory SQLite database (per test function)
  - an HTTPX AsyncClient wired to the FastAPI app via ASGITransport
  - helper factories to create and authenticate users
"""
from __future__ import annotations

import sys
import os

# Ensure backend/ is on sys.path so `from app...` imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationKind


# ── Per-test isolated in-memory database ──────────────────────────────────

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """HTTPX AsyncClient backed by in-memory DB via dependency override."""

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── User factories ─────────────────────────────────────────────────────────

async def _create_user(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    password: str = "Password1",
    display_name: str | None = None,
    role: str = UserRole.member.value,
    is_active: bool = True,
    is_verified: bool = True,
) -> User:
    user = User(
        email=email,
        username=username,
        display_name=display_name or username,
        hashed_password=hash_password(password),
        role=role,
        is_active=is_active,
        is_verified=is_verified,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def member_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session, email="member@example.com", username="member1"
    )


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session, email="second@example.com", username="member2"
    )


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session,
        email="admin@example.com",
        username="admin1",
        role=UserRole.admin.value,
    )


@pytest_asyncio.fixture
async def moderator_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session,
        email="mod@example.com",
        username="mod1",
        role=UserRole.moderator.value,
    )


# ── Token helpers ──────────────────────────────────────────────────────────

def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id), {"role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_headers(member_user: User) -> dict[str, str]:
    return auth_headers(member_user)


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    return auth_headers(admin_user)


@pytest.fixture
def moderator_headers(moderator_user: User) -> dict[str, str]:
    return auth_headers(moderator_user)


# ── Notification factory ───────────────────────────────────────────────────

async def create_test_notification(
    db: AsyncSession,
    recipient: User,
    kind: NotificationKind = NotificationKind.system,
    title: str = "Test notification",
) -> Notification:
    n = Notification(
        recipient_id=recipient.id,
        kind=kind.value,
        title=title,
        is_read=False,
    )
    db.add(n)
    await db.flush()
    await db.refresh(n)
    return n

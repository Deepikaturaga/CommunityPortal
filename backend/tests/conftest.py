"""Shared pytest fixtures for the backend test suite.

Uses aiosqlite as an in-process database so tests run without Postgres.
The async SQLite engine is created fresh for each test session.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import create_app

# ---------------------------------------------------------------------------
# In-memory SQLite engine (per test session)
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():  # type: ignore[no-untyped-def]
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture()
async def db_session(engine):  # type: ignore[no-untyped-def]
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
        await session.rollback()  # isolate every test


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncClient:  # type: ignore[misc]
    app = create_app()

    async def _override_get_db() -> AsyncSession:  # type: ignore[misc]
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    ) as ac:
        yield ac  # type: ignore[misc]


# ---------------------------------------------------------------------------
# JWT token helpers
# ---------------------------------------------------------------------------


def _make_token(role: str) -> str:
    return create_access_token({"sub": f"user-{role}", "role": role})


@pytest.fixture()
def viewer_token() -> str:
    return _make_token("viewer")


@pytest.fixture()
def editor_token() -> str:
    return _make_token("editor")


@pytest.fixture()
def admin_token() -> str:
    return _make_token("admin")

"""
Shared pytest fixtures for integration tests.

- In-memory SQLite via aiosqlite (no external DB needed in CI)
- Fake Redis backed by fakeredis if available, otherwise real redis-py against
  a real server; tests skip gracefully if neither is available.
- HTTPX AsyncClient using ASGITransport
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_async_session
from app.core.redis_client import get_redis
from app.main import create_app

# ---------------------------------------------------------------------------
# Event-loop policy for pytest-asyncio 0.24
# ---------------------------------------------------------------------------
pytest_plugins = ("pytest_asyncio",)


# ---------------------------------------------------------------------------
# In-memory DB
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


# ---------------------------------------------------------------------------
# Fake Redis (pure in-process dict-backed implementation for unit tests)
# ---------------------------------------------------------------------------

class FakeRedis:
    """Minimal Redis subset sufficient for the rate-limiter Lua script."""

    def __init__(self) -> None:
        self._store: dict[str, int] = {}
        self._ttl: dict[str, int] = {}

    async def eval(self, script: str, numkeys: int, *args: Any) -> list[int]:
        key = args[0]
        window = int(args[1])
        current = self._store.get(key, 0) + 1
        self._store[key] = current
        if key not in self._ttl:
            self._ttl[key] = window
        return [current, self._ttl[key]]

    async def aclose(self) -> None:
        pass

    def reset(self) -> None:
        self._store.clear()
        self._ttl.clear()


@pytest.fixture()
def fake_redis() -> FakeRedis:
    return FakeRedis()


# ---------------------------------------------------------------------------
# ASGI test client with overridden dependencies
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def client(
    async_db_session: AsyncSession,
    fake_redis: FakeRedis,
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    app.dependency_overrides[get_async_session] = lambda: _yield_session(async_db_session)
    app.dependency_overrides[get_redis] = lambda: fake_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


async def _yield_session(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    yield session

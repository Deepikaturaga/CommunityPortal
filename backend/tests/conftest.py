"""Shared pytest fixtures."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base
from app.models.searchable_record import SearchableRecord
from tests.doubles.in_memory_search import InMemorySearchClient

# ── In-memory SQLite engine for tests ─────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
def search_client() -> InMemorySearchClient:
    return InMemorySearchClient()


# ── Factory helpers ────────────────────────────────────────────────────────────


async def make_record(
    session: AsyncSession,
    *,
    index_name: str = "products",
    document_type: str = "product",
    payload: dict | None = None,
    is_active: bool = True,
    title: str | None = None,
) -> SearchableRecord:
    record = SearchableRecord(
        id=str(uuid.uuid4()),
        index_name=index_name,
        document_type=document_type,
        payload=payload or {"name": f"record-{uuid.uuid4().hex[:6]}"},
        title=title,
        is_active=is_active,
    )
    session.add(record)
    await session.flush()
    return record

"""Async SQLAlchemy engine + session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str | None = None):
    settings = get_settings()
    db_url = url or settings.database_url
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    return create_async_engine(db_url, echo=False, connect_args=connect_args)


# Module-level engine – overridden in tests via dependency override
_engine = _make_engine()
_session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session


async def create_all_tables() -> None:
    """Create all tables (dev/test only)."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Drop all tables (test only)."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

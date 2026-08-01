from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine() -> tuple[
    "create_async_engine.__class__",  # type: ignore[name-defined]
    async_sessionmaker[AsyncSession],
]:
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


_engine, _session_factory = _make_engine()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session

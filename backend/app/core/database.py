"""Async SQLAlchemy engine + session factory (single canonical instance)."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine() -> object:  # returns AsyncEngine; typed loosely to avoid import cycle
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.environment == "development",
        pool_pre_ping=True,
    )


_engine = _make_engine()
_async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,  # type: ignore[arg-type]
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one session per request."""
    async with _async_session_factory() as session:
        yield session

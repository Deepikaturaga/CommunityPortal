"""Async SQLAlchemy 2.0 engine + session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Canonical declarative base for all ORM models."""


def _build_engine() -> "create_async_engine":  # type: ignore[return]
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.app_env == "development",
        pool_pre_ping=True,
    )


_engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a scoped AsyncSession."""
    async with AsyncSessionLocal() as session:
        yield session


async def close_engine() -> None:
    """Called on application shutdown."""
    await _engine.dispose()

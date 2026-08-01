"""SQLAlchemy 2.0 async engine + session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

_engine = create_async_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    echo=get_settings().debug,
)

_AsyncSessionLocal = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a scoped async DB session."""
    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Convenience type-alias for injection
DbSession = Annotated[AsyncSession, Depends(get_db)]

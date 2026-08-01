"""ASGI entrypoint — single canonical FastAPI application."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.services.posts.comments_router import router as comments_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging()
    # Validate settings eagerly at startup (pydantic-settings raises on bad config)
    _ = settings
    yield
    # Shutdown: SQLAlchemy engine disposal handled per-request via DI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Posts Service",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────────────────
    app.include_router(comments_router, prefix="/v1")

    # ── Health ───────────────────────────────────────────────────────────────
    @app.get("/health", tags=["ops"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

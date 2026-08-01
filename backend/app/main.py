from __future__ import annotations

"""Canonical ASGI entrypoint — one app, one router chain."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.routers.reply_router import router as replies_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Validate settings at startup; fail fast on misconfiguration.
    get_settings()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Discussion API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(replies_router, prefix="/api/v1")

    @app.get("/healthz", tags=["ops"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

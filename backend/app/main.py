"""ASGI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.services.search.router import router as search_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: validate config eagerly (raises on misconfiguration)
    get_settings()
    yield
    # Shutdown: nothing to tear down for the DB pool in this slice


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="API",
        version="1.0.0",
        debug=settings.debug,
        # Hide /docs + /openapi.json in production
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],  # Tighten per deployment; default deny
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    register_exception_handlers(app)

    # Routers
    app.include_router(search_router, prefix="/api/v1")

    # Health / readiness
    @app.get("/health", include_in_schema=False)
    async def _health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

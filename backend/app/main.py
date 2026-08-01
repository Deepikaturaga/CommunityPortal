"""ASGI application entry-point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import create_all_tables
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    conflict_handler,
    forbidden_handler,
    not_found_handler,
)
from app.routers.admin_router import router as admin_router
from app.routers.auth_router import router as auth_router
from app.routers.profile_router import router as profile_router
from app.routers.taxonomy_router import router as taxonomy_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Dev/test convenience – create tables on startup
    await create_all_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Backend API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS – tighten in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handlers
    app.add_exception_handler(NotFoundError, not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ForbiddenError, forbidden_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ConflictError, conflict_handler)  # type: ignore[arg-type]

    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(profile_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)
    app.include_router(taxonomy_router, prefix=api_prefix)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

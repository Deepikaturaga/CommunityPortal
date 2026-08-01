"""
Canonical ASGI entrypoint.

Lifespan:
  startup  – (nothing to do; engine + Redis are lazily initialised)
  shutdown – dispose DB engine + close Redis connection pool

Middleware stack (outermost → innermost):
  1. RateLimitHeaderMiddleware – attaches RateLimit-* headers
  2. (future: CORS, trusted-host, etc.)

Routers:
  /api/v1/auth     – registration, login
  /api/v1/content  – content CRUD
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import close_engine
from app.core.exceptions import AppError, app_error_handler
from app.core.redis_client import close_redis
from app.middleware.ratelimit_headers import RateLimitHeaderMiddleware
from app.routers.auth_router import router as auth_router
from app.routers.content_router import router as content_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    # startup
    yield
    # shutdown
    await close_engine()
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Application API",
        version="1.0.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    # NOTE: CORS origins must be configured per-deployment; default deny-all.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.add_middleware(RateLimitHeaderMiddleware)

    # ── Global error handler ──────────────────────────────────────────────────
    application.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    # ── Routers ───────────────────────────────────────────────────────────────
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(content_router, prefix="/api/v1")

    # ── Health ────────────────────────────────────────────────────────────────
    @application.get("/health", tags=["ops"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()

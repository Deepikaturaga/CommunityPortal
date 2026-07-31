from backend.app.middleware.security_headers import SecurityHeadersMiddleware
    # Security headers
    # ------------------------------------------------------------------ #
    app.add_middleware(
        SecurityHeadersMiddleware,
        app_env=settings.app_env,
    )

    # ------------------------------------------------------------------ #
"""
Minimal FastAPI application entrypoint.

Wires the ElastiCache connection pool via lifespan so every request has
access to a live, shared pool via ``app.state.redis_pool``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.services.identity.session_store import create_redis_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    # Validate that production/staging use TLS
    redis_url = settings.redis_url.get_secret_value()
    if settings.app_env != "development" and not redis_url.startswith("rediss://"):
        logger.warning(
            "ElastiCache connection is NOT using TLS (rediss://) in env=%s. "
            "Enable in-transit encryption on the ElastiCache cluster and update redis_url.",
            settings.app_env,
        )

    if settings.app_env == "production" and not settings.session_cookie_secure:
        raise RuntimeError("session_cookie_secure MUST be True in production.")

    pool = create_redis_pool(settings)
    app.state.redis_pool = pool
    logger.info("Redis connection pool created (env=%s).", settings.app_env)

    yield

    await pool.disconnect()
    logger.info("Redis connection pool closed.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS — restrict in production; open only in development
    if settings.app_env == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # ------------------------------------------------------------------ #
    # Routers
    # ------------------------------------------------------------------ #
    # Additional routers (auth, users, …) are included here as they are
    # implemented in subsequent phases.

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

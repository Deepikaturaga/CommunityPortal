"""Canonical ASGI entry-point (COMP-012 - API Edge Gateway).

Middleware stack (outermost -> innermost):
  1. SecurityHeadersMiddleware  - HSTS, CSP, X-Frame-Options, etc.
  2. CORSMiddleware             - cross-origin policy

Order is deliberate: security headers are added to **every** response, including
CORS pre-flight 200/204 responses, so SecurityHeadersMiddleware wraps CORS.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers.health import router as health_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # pragma: no cover
    """Application lifespan - place startup/shutdown resource init here."""
    settings: Settings = app.state.settings
    logger.info(
        "API Edge starting. env=%s https_proxy=%s",
        settings.app_env,
        settings.https_behind_proxy,
    )
    yield
    logger.info("API Edge shutting down.")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Factory that wires the full middleware stack; injectable for tests."""
    cfg = settings or get_settings()

    app = FastAPI(
        title="API Edge Gateway",
        version="0.1.0",
        # Disable Swagger/ReDoc in production to reduce attack surface.
        docs_url="/docs" if cfg.app_env != "production" else None,
        redoc_url="/redoc" if cfg.app_env != "production" else None,
        openapi_url="/openapi.json" if cfg.app_env != "production" else None,
        lifespan=lifespan,
    )

    # Stash for lifespan and tests.
    app.state.settings = cfg

    # add_middleware() inserts at position 0 (outermost); last call = outermost.
    # We add CORS first so it ends up *inside* SecurityHeaders in call order.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_allow_origins,
        allow_credentials=cfg.cors_allow_credentials,
        allow_methods=cfg.cors_allow_methods,
        allow_headers=cfg.cors_allow_headers,
    )

    app.add_middleware(SecurityHeadersMiddleware, settings=cfg)

    app.include_router(health_router)

    return app


# Module-level app instance used by uvicorn / gunicorn.
app = create_app()

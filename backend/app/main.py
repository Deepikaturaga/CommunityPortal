from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.event_bus import get_event_bus
from app.services.search.indexer import create_indexer
from app.services.search.subscriber import register_search_subscriber

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    cfg = get_settings()
    configure_logging(cfg.log_level)

    if cfg.environment == "production" and (
        cfg.secret_key.get_secret_value() == "change-me-in-production"
    ):
        raise RuntimeError("SECRET_KEY must be changed in production")

    # Bootstrap search indexer and wire subscriber.
    indexer = await create_indexer(cfg)
    bus = get_event_bus()
    register_search_subscriber(bus, indexer)

    logger.info("app.startup", environment=cfg.environment)
    yield

    # Graceful shutdown.
    await indexer._os.close()
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(
        title="Content API",
        version="1.0.0",
        docs_url="/api/docs" if cfg.environment != "production" else None,
        redoc_url="/api/redoc" if cfg.environment != "production" else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if cfg.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ────────────────────────────────────────────────────────────────
    from app.routers import health  # noqa: PLC0415

    app.include_router(health.router, prefix="/api")

    return app


app = create_app()

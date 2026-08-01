"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import close_engine
from app.core.logging import configure_logging
from app.services.identity.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    get_settings()  # validate config at startup — raises on misconfiguration
    yield
    await close_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="API",
        version="1.0.0",
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url="/api/redoc" if settings.environment != "production" else None,
        openapi_url="/api/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # CORS — tighten origins per deployment environment
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[] if settings.environment == "production" else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    api_v1_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_v1_prefix)

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

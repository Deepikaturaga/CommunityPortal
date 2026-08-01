"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import validation_exception_handler
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: settings are validated here (raises on misconfiguration).
    get_settings()
    yield
    # Shutdown: nothing to teardown for now.


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="API",
        version="1.0.0",
        docs_url="/api/docs" if settings.app_env != "production" else None,
        redoc_url="/api/redoc" if settings.app_env != "production" else None,
        openapi_url="/api/openapi.json" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.allowed_hosts],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    application.include_router(auth.router, prefix="/api/v1")

    return application


app = create_app()

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import _get_engine


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: warm the engine pool (validates DSN early)
    _get_engine()
    yield
    # Shutdown: dispose engine
    engine = _get_engine()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Content Moderation API",
        version="1.0.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Global exception handler — never leak internals
    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred."},
        )

    # Routers
    from app.api.admin_router import router as admin_router  # noqa: PLC0415

    application.include_router(admin_router, prefix="/api/v1")

    # Health check
    @application.get("/health", tags=["ops"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()

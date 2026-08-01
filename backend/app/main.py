"""
Canonical ASGI application entrypoint.

One FastAPI instance, one lifespan, all routers registered here.
"""
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.core.logging import configure_logging

# Routers
from app.auth.router import router as auth_router
from app.kb.kb_router import router as kb_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    yield
    # Shutdown: engine disposal handled at process exit; add explicit cleanup here if needed.


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="KB API",
        version="1.0.0",
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url="/api/redoc" if settings.environment != "production" else None,
        openapi_url="/api/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Global exception handlers (no internal detail leakage)
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    application.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

    # Routers
    api_prefix = "/api/v1"
    application.include_router(auth_router, prefix=api_prefix)
    application.include_router(kb_router, prefix=api_prefix)

    @application.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()

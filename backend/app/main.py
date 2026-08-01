"""FastAPI application entry-point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import engine
from app.routers.media_router import router as media_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Validate settings at startup — raises on bad config
    get_settings()
    yield
    # Graceful shutdown: dispose the async engine connection pool
    await engine.dispose()


app = FastAPI(
    title="Backend API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── Global exception handlers ──────────────────────────────────────────────────


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a generic 500 without leaking internals (OWASP A05)."""
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(media_router, prefix="/api/v1")


# ── Health / readiness ─────────────────────────────────────────────────────────


@app.get("/health", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}

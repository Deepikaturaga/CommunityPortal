"""ASGI application entry-point — canonical FastAPI app (single root)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.models.base import Base

# Ensure all models are registered with Base.metadata before lifespan
import app.models.user  # noqa: F401
import app.models.content  # noqa: F401
import app.models.moderation  # noqa: F401

from app.services.moderation.router import router as moderation_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create tables in dev/test; in production use Alembic migrations."""
    if settings.ENVIRONMENT in ("development", "test"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Moderation Service",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)


# ---------------------------------------------------------------------------
# Global exception handlers — never leak internals
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the full traceback (structured logger would go here in production)
    import logging
    logging.getLogger(__name__).exception("Unhandled error: %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(moderation_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}

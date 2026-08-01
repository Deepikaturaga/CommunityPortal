from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import engine
from app.core.logging import configure_logging
from app.services.notifications.router import router as notifications_router

configure_logging()
logger: structlog.BoundLogger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", event="api_startup")
    yield
    logger.info("shutdown", event="api_shutdown")
    await engine.dispose()


app = FastAPI(
    title="Notification Preference API",
    version="1.0.0",
    description="COMP-008 – notification preference and list API (IF-010)",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS (locked down – override via env/config for prod) ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],   # deny all cross-origin by default; override in deployment config
    allow_credentials=False,
    allow_methods=["GET", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Global exception handler – no internal details leaked ─────────────────────
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, exc=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(notifications_router, prefix="/api/v1")


# ── Health / readiness ─────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"], status_code=status.HTTP_200_OK)
async def health() -> dict[str, str]:
    return {"status": "ok"}

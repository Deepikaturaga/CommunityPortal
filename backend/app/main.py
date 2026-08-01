from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import create_all_tables
from app.core.exceptions import AppError
from app.routers.auth import router as auth_router, users_router
from app.routers.discussions import router as discussions_router, posts_router
from app.routers.kb import router as kb_router
from app.routers.search import router as search_router
from app.routers.notifications import router as notifications_router
from app.routers.admin import router as admin_router

# Ensure models are imported so metadata is populated
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    await create_all_tables()
    yield


app = FastAPI(
    title="Community Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global error handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Routers ────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)
app.include_router(discussions_router, prefix=PREFIX)
app.include_router(posts_router, prefix=PREFIX)
app.include_router(kb_router, prefix=PREFIX)
app.include_router(search_router, prefix=PREFIX)
app.include_router(notifications_router, prefix=PREFIX)
app.include_router(admin_router, prefix=PREFIX)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict:
    return {"status": "ready"}

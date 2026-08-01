"""ASGI application entrypoint — canonical app.main:app."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings  # validates config at import time
from app.core.database import engine, Base
from app.services.profile.router import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create tables on startup (dev/test); close engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Member API",
    version="1.0.0",
    lifespan=lifespan,
    # Never expose internal tracebacks in responses
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url=None,
)

# CORS — restrictive by default; override via env/settings in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],       # explicit origins only — no wildcard
    allow_credentials=True,
    allow_methods=["GET", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Global error handler — never leak internal details ────────────────────────
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(profile_router, prefix="/api/v1")


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}

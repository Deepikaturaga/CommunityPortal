from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover
    # Startup: initialise shared resources here (DB engine, HTTP client pool, etc.)
    yield
    # Shutdown: release shared resources here


app = FastAPI(
    title="Backend API",
    version="0.1.0",
    lifespan=lifespan,
    # Disable docs on non-development environments via settings in a real deployment
)


@app.get("/health", tags=["ops"], response_class=JSONResponse)
async def health() -> dict[str, str]:
    """Liveness probe — returns 200 when the process is running."""
    return {"status": "ok"}


@app.get("/ready", tags=["ops"], response_class=JSONResponse)
async def ready() -> dict[str, str]:
    """Readiness probe — extend to check DB connectivity before returning ok."""
    return {"status": "ready"}

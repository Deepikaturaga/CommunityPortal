"""
FastAPI application entry-point.

Middleware registration order (outermost → innermost at runtime):
    SecurityHeadersMiddleware  ← applied last, wraps everything
    CSRFMiddleware             ← validates tokens for mutating requests
    … auth / other middleware …
    Routes

Because Starlette applies add_middleware() in LIFO order, SecurityHeaders must be
added *after* CSRF so it becomes the outermost wrapper.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.csrf import CSRFMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup: env=%s debug=%s", settings.APP_ENV, settings.DEBUG)
    yield
    logger.info("shutdown")


app = FastAPI(
    title="Backend API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# CORS — must be registered before CSRF middleware
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token"],
    expose_headers=["X-CSRF-Token"],
)

# ------------------------------------------------------------------
# CSRF protection (inner; validates tokens on mutating requests)
# ------------------------------------------------------------------
app.add_middleware(CSRFMiddleware)

# ------------------------------------------------------------------
# Security headers (outer; stamps headers on every response including
# CSRF-rejected 403s)
# ------------------------------------------------------------------
app.add_middleware(SecurityHeadersMiddleware)


# ------------------------------------------------------------------
# Health / readiness (exempt from CSRF — GET methods)
# ------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readiness", tags=["ops"])
async def readiness() -> dict[str, str]:
    return {"status": "ready"}

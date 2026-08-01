"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.auth_router import router as auth_router


def create_app(settings=None) -> FastAPI:  # type: ignore[no-untyped-def]
    cfg = settings or get_settings()
    app = FastAPI(
        title=cfg.app_name,
        version="1.0.0",
        docs_url="/docs" if cfg.debug else None,
        redoc_url="/redoc" if cfg.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],  # explicitly empty — must be configured per deployment
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )

    app.include_router(auth_router)

    @app.get("/health")
    async def health() -> dict:  # type: ignore[type-arg]
        return {"status": "ok"}

    return app


app = create_app()

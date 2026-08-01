from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
import app.models.content  # noqa: F401  — register mapper
import app.models.kb_article  # noqa: F401  — register mapper
import app.models.moderation  # noqa: F401  — register mapper
import app.models.user  # noqa: F401  — register mapper
from app.services.kb.router import router as kb_router
from app.services.kb.visibility import router as kb_visibility_router

# Optional routers implemented in sibling phases; safe to skip when absent.
try:
    from app.services.moderation.router import router as moderation_router  # type: ignore[import]

    _has_moderation = True
except ModuleNotFoundError:
    _has_moderation = False

try:
    from app.services.posts.router import router as posts_router  # type: ignore[import]

    _has_posts = True
except ModuleNotFoundError:
    _has_posts = False


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    if settings.ENVIRONMENT in ("development", "test"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Moderation Service", version="0.1.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging

    logging.getLogger(__name__).exception(
        "Unhandled error: %s %s", request.method, request.url
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


if _has_moderation:
    app.include_router(
        moderation_router,  # type: ignore[possibly-undefined]
        prefix="/api/v1",
    )
if _has_posts:
    app.include_router(
        posts_router,  # type: ignore[possibly-undefined]
        prefix="/api/v1",
    )
app.include_router(kb_router, prefix="/api/v1")
app.include_router(kb_visibility_router, prefix="/api/v1")


@app.get("/health", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}

"""Global exception handlers — no internal detail leakage."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


def _error(code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=code, content={"detail": message})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(404)
    async def not_found(_req: Request, _exc: Exception) -> JSONResponse:
        return _error(status.HTTP_404_NOT_FOUND, "Resource not found")

    @app.exception_handler(405)
    async def method_not_allowed(_req: Request, _exc: Exception) -> JSONResponse:
        return _error(status.HTTP_405_METHOD_NOT_ALLOWED, "Method not allowed")

    @app.exception_handler(500)
    async def internal(_req: Request, exc: Exception) -> JSONResponse:
        # Log without leaking exc.args to the response
        return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")

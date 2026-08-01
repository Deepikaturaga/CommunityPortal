"""Shared error handling and response envelope."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def _validation_error_handler(
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(include_url=False)},
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        # Never leak internals; log correlation id in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

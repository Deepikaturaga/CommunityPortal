"""Shared exception types and global HTTP error handler."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class AppError(Exception):
    """Base class for application domain errors."""

    status_code: int = HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = HTTP_404_NOT_FOUND
    detail = "Resource not found"


class ConflictError(AppError):
    status_code = HTTP_409_CONFLICT
    detail = "Resource already exists"


class UnauthorizedError(AppError):
    status_code = HTTP_401_UNAUTHORIZED
    detail = "Authentication required"


class ForbiddenError(AppError):
    status_code = HTTP_403_FORBIDDEN
    detail = "Access denied"


class ValidationError(AppError):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation failed"


class BadRequestError(AppError):
    status_code = HTTP_400_BAD_REQUEST
    detail = "Bad request"


class RateLimitError(AppError):
    """Raised when a per-account rate limit threshold is exceeded (AC-031.2)."""

    status_code = HTTP_429_TOO_MANY_REQUESTS
    # Generic message – intentionally does not reveal internal limits (AC-031.2)
    detail = "Too many requests. Please try again later."


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert AppError subclasses to JSON responses without leaking internals."""
    if isinstance(exc, AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    # Unhandled – return generic 500 without traceback leakage
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

"""Shared exception types and global handlers."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    def __init__(self, detail: str = "Not found") -> None:
        self.detail = detail


class ForbiddenError(Exception):
    def __init__(self, detail: str = "Forbidden") -> None:
        self.detail = detail


class ConflictError(Exception):
    def __init__(self, detail: str = "Conflict") -> None:
        self.detail = detail


async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.detail})


async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.detail})


async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.detail})

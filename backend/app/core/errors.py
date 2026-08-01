"""Standardised error response shapes and exception handlers."""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    errors: list[ErrorDetail]


def _err(code: str, message: str, field: str | None = None) -> dict:  # type: ignore[type-arg]
    return {"errors": [{"code": code, "message": message, "field": field}]}


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for e in exc.errors():
        loc = e.get("loc", ())
        field = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else None
        errors.append(
            {"code": "validation_error", "message": e["msg"], "field": field}
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"errors": errors},
    )

"""Health / readiness endpoints (ALB target health-check compatible)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["ops"])


class HealthResponse(BaseModel):
    status: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=200,
    summary="Liveness probe",
    # ALB health-checks arrive over plain HTTP on the private subnet; the
    # SecurityHeadersMiddleware explicitly bypasses the HTTPS redirect for
    # this path so the check always succeeds regardless of TLS config.
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/healthz", response_model=HealthResponse, status_code=200, include_in_schema=False)
async def healthz() -> HealthResponse:  # alias
    return HealthResponse(status="ok")

"""
COMP-006 Moderation Report Intake — HTTP router (IF-008).

Routes
------
POST   /moderation/reports          → 201 ReportResponse  | 409 on duplicate
GET    /moderation/reports          → 200 ReportListResponse
GET    /moderation/reports/{id}     → 200 ReportResponse  | 404
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.moderation.reports import ModerationReportService
from app.services.moderation.schemas import (
    ReportCreate,
    ReportListResponse,
    ReportResponse,
)

router = APIRouter(prefix="/moderation/reports", tags=["moderation"])


def _svc(db: AsyncSession = Depends(get_db)) -> ModerationReportService:
    return ModerationReportService(db)


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a moderation report (IF-008 / COMP-006)",
    responses={
        409: {"description": "Duplicate report for this (reporter_id, target_id) pair."},
        403: {"description": "Reporter and target must be different users."},
    },
)
async def create_report(
    payload: ReportCreate,
    svc: ModerationReportService = Depends(_svc),
) -> ReportResponse:
    """
    Submit a new moderation report.

    Returns **HTTP 409** when a report from the same ``reporter_id``
    against the same ``target_id`` already exists (AC-015.2).
    """
    return await svc.create_report(payload)


@router.get(
    "",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="List moderation reports",
)
async def list_reports(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    svc: ModerationReportService = Depends(_svc),
) -> ReportListResponse:
    items, total = await svc.list_reports(offset=offset, limit=limit)
    return ReportListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch a single moderation report",
    responses={404: {"description": "Report not found."}},
)
async def get_report(
    report_id: str,
    svc: ModerationReportService = Depends(_svc),
) -> ReportResponse:
    return await svc.get_report(report_id)

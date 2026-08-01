"""HTTP router exposing reconciliation trigger and status endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import AsyncSession, get_db
from app.core.search_client import OpenSearchAdapter, get_search_client
from services.search.reconcile import BatchResult, ReconciliationReport, SearchReconciler
from services.search.scheduler import get_scheduler, run_reconciliation_job

router = APIRouter(prefix="/search/reconcile", tags=["search-reconcile"])


# ── Pydantic response schemas ─────────────────────────────────────────────────


class BatchResultSchema(BaseModel):
    batch_number: int
    records_processed: int
    upserted: int
    failed: int
    errors: list[str]

    @classmethod
    def from_domain(cls, b: BatchResult) -> "BatchResultSchema":
        return cls(
            batch_number=b.batch_number,
            records_processed=b.records_processed,
            upserted=b.upserted,
            failed=b.failed,
            errors=b.errors,
        )


class ReconciliationReportSchema(BaseModel):
    run_id: uuid.UUID
    started_at: str
    finished_at: str | None
    index_name: str
    total_source_records: int
    total_upserted: int
    total_failed: int
    orphans_removed: int
    duration_seconds: float | None
    success: bool
    error: str | None
    batches: list[BatchResultSchema]

    @classmethod
    def from_domain(cls, r: ReconciliationReport) -> "ReconciliationReportSchema":
        return cls(
            run_id=r.run_id,
            started_at=r.started_at.isoformat(),
            finished_at=r.finished_at.isoformat() if r.finished_at else None,
            index_name=r.index_name,
            total_source_records=r.total_source_records,
            total_upserted=r.total_upserted,
            total_failed=r.total_failed,
            orphans_removed=r.orphans_removed,
            duration_seconds=r.duration_seconds,
            success=r.success,
            error=r.error,
            batches=[BatchResultSchema.from_domain(b) for b in r.batches],
        )


class TriggerRequest(BaseModel):
    index_name: str = Field(default="default", min_length=1, max_length=255)
    batch_size: int = Field(
        default=settings.reindex_batch_size,
        gt=0,
        le=10_000,
    )


class SchedulerStatusSchema(BaseModel):
    running: bool
    jobs: list[dict[str, Any]]


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/trigger",
    response_model=ReconciliationReportSchema,
    status_code=status.HTTP_200_OK,
    summary="Manually trigger a full search index reconciliation",
    description=(
        "Runs the idempotent full-reindex job synchronously and returns the "
        "reconciliation report.  Safe to call multiple times — a second run "
        "against an already-correct index is a no-op."
    ),
)
async def trigger_reconciliation(
    body: TriggerRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    search: Annotated[OpenSearchAdapter, Depends(get_search_client)],
) -> ReconciliationReportSchema:
    reconciler = SearchReconciler(
        db=db,
        search=search,
        index_name=body.index_name,
        batch_size=body.batch_size,
    )
    report = await reconciler.run()
    if not report.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=report.error or "Reconciliation failed",
        )
    return ReconciliationReportSchema.from_domain(report)


@router.get(
    "/scheduler/status",
    response_model=SchedulerStatusSchema,
    summary="Return scheduler status and registered jobs",
)
async def scheduler_status() -> SchedulerStatusSchema:
    scheduler = get_scheduler()
    if scheduler is None or not scheduler.running:
        return SchedulerStatusSchema(running=False, jobs=[])
    jobs = [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        for job in scheduler.get_jobs()
    ]
    return SchedulerStatusSchema(running=True, jobs=jobs)

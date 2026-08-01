"""
COMP-006 report intake service.

Business rules
--------------
* AC-015.2: duplicate (reporter_id, target_id) → ConflictError → HTTP 409.
* A reporter may not report themselves (self-report guard).
* Duplicate detection is enforced at both the DB layer (unique constraint)
  and the service layer (explicit pre-check) for a clear 409 error message
  rather than a raw integrity-error 500.
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.services.moderation.models import ModerationReport, ReportStatus
from app.services.moderation.schemas import ReportCreate, ReportResponse


class ModerationReportService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Intake ────────────────────────────────────────────────────────────────

    async def create_report(self, payload: ReportCreate) -> ReportResponse:
        """
        Accept a new moderation report.

        Raises
        ------
        ForbiddenError  — reporter and target are the same user.
        ConflictError   — a report from reporter_id against target_id already
                          exists (AC-015.2 → HTTP 409).
        """
        if payload.reporter_id == payload.target_id:
            raise ForbiddenError("A user may not report themselves.")

        # Explicit pre-check (fast path) — avoids relying solely on DB error
        existing = await self._db.scalar(
            select(ModerationReport).where(
                ModerationReport.reporter_id == payload.reporter_id,
                ModerationReport.target_id == payload.target_id,
            )
        )
        if existing is not None:
            raise ConflictError(
                f"A report from reporter {payload.reporter_id!r} against "
                f"target {payload.target_id!r} already exists."
            )

        report = ModerationReport(
            id=str(uuid.uuid4()),
            reporter_id=payload.reporter_id,
            target_id=payload.target_id,
            reason=payload.reason.value,
            description=payload.description,
            status=ReportStatus.PENDING.value,
        )
        self._db.add(report)

        try:
            await self._db.commit()
            await self._db.refresh(report)
        except IntegrityError as exc:
            await self._db.rollback()
            # Race-condition guard: another request beat us to the unique slot.
            raise ConflictError(
                f"A report from reporter {payload.reporter_id!r} against "
                f"target {payload.target_id!r} already exists."
            ) from exc

        return ReportResponse.model_validate(report)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_report(self, report_id: str) -> ReportResponse:
        row = await self._db.get(ModerationReport, report_id)
        if row is None:
            raise NotFoundError(f"Report {report_id!r} not found.")
        return ReportResponse.model_validate(row)

    async def list_reports(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ReportResponse], int]:
        count_q = select(func.count()).select_from(ModerationReport)
        total: int = await self._db.scalar(count_q) or 0

        rows_q = (
            select(ModerationReport)
            .order_by(ModerationReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(rows_q)
        rows = result.scalars().all()
        return [ReportResponse.model_validate(r) for r in rows], total

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import AdminUser
from app.services.admin.dashboard import get_dashboard_aggregates
from app.services.admin.schemas import DashboardResponse

router = APIRouter(prefix="/admin", tags=["admin"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Admin dashboard aggregates",
    description=(
        "Returns aggregated figures for accounts, content volume, and moderation stats. "
        "Requires admin role (IF-011 / COMP-009)."
    ),
)
async def dashboard(
    _admin: AdminUser,
    db: DbDep,
) -> DashboardResponse:
    """
    Admin-only endpoint — returns a platform-wide aggregate snapshot.

    * ``accounts``   — total users, status/role breakdown, new registrations (30 days)
    * ``content``    — total items, status breakdown, new items (30 days)
    * ``moderation`` — total actions, verdict breakdown, queue depth (pending items)
    """
    return await get_dashboard_aggregates(db)

"""Scheduler for the search reconciliation job.

Uses APScheduler with an asyncio backend.  The scheduler is attached to the
FastAPI lifespan so it starts when the app starts and shuts down cleanly.

The job can also be triggered manually via the HTTP trigger endpoint.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.search_client import get_search_client
from services.search.reconcile import ReconciliationReport, SearchReconciler

logger = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def run_reconciliation_job(
    index_name: str,
    *,
    batch_size: int = settings.reindex_batch_size,
) -> ReconciliationReport:
    """Execute a full reconciliation run; suitable for direct await or scheduler dispatch."""
    async with AsyncSessionLocal() as session:
        reconciler = SearchReconciler(
            db=session,
            search=get_search_client(),
            index_name=index_name,
            batch_size=batch_size,
        )
        return await reconciler.run()


def _make_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    if settings.reindex_cron_enabled:
        scheduler.add_job(
            run_reconciliation_job,
            CronTrigger(
                hour=settings.reindex_cron_hour,
                minute=settings.reindex_cron_minute,
            ),
            kwargs={"index_name": "default"},
            id="search_reindex",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        logger.info(
            "reconciliation.scheduler_configured",
            hour=settings.reindex_cron_hour,
            minute=settings.reindex_cron_minute,
        )
    return scheduler


@asynccontextmanager
async def scheduler_lifespan() -> AsyncGenerator[None, None]:
    """Async context manager suitable for inclusion in a FastAPI lifespan."""
    global _scheduler
    _scheduler = _make_scheduler()
    _scheduler.start()
    logger.info("reconciliation.scheduler_started")
    try:
        yield
    finally:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("reconciliation.scheduler_stopped")


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler

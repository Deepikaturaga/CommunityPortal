"""Search index reconciliation service.

Provides idempotent full-reindex logic that rebuilds the search index from
the canonical source store (``searchable_records`` table) without duplication.

Design decisions
----------------
* **Idempotency via upsert** — every document is indexed with a deterministic
  document-id equal to the record's string UUID.  A second run upserts the
  same payload; the resulting index state is identical.
* **Batched bulk upsert** — records are streamed in configurable batches with
  keyset pagination (ordered by ``id``) to avoid unbounded memory growth.
* **Orphan pruning** — after upserting all active rows the job queries the
  search cluster for document IDs *not* present in the DB (or whose DB row is
  now inactive) and removes them, keeping the index consistent.
* **Structured audit log** — every run emits a ``ReconciliationReport`` so
  callers (scheduler or HTTP trigger) can inspect the outcome.
* **No mutation of already-applied state** — running the job a second time
  against an already-correct index produces zero net changes (all upserts are
  no-ops at the cluster level; the orphan check finds no stale IDs).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.search_client import SearchClientProtocol
from app.models.searchable_record import SearchableRecord

logger = get_logger(__name__)


# ── Result types ──────────────────────────────────────────────────────────────


@dataclass
class BatchResult:
    """Outcome of processing a single batch."""

    batch_number: int
    records_processed: int
    upserted: int
    failed: int
    errors: list[str] = field(default_factory=list)


@dataclass
class ReconciliationReport:
    """Aggregate outcome of a full reconciliation run."""

    run_id: uuid.UUID
    started_at: datetime
    finished_at: datetime | None = None
    index_name: str = ""
    total_source_records: int = 0
    total_upserted: int = 0
    total_failed: int = 0
    orphans_removed: int = 0
    batches: list[BatchResult] = field(default_factory=list)
    success: bool = False
    error: str | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _payload_hash(payload: dict[str, Any]) -> str:
    """Stable SHA-256 of a JSON-serialised payload (sorted keys)."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _build_upsert_actions(
    records: list[SearchableRecord],
    index_name: str,
) -> list[dict[str, Any]]:
    """Build opensearch-py bulk API action list for an upsert (index) operation."""
    actions: list[dict[str, Any]] = []
    for record in records:
        # record.id is stored as str(uuid) in the DB.
        actions.append({"index": {"_index": index_name, "_id": str(record.id)}})
        actions.append(record.payload)
    return actions


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


# ── Core reconciler ───────────────────────────────────────────────────────────


class SearchReconciler:
    """Full-reindex reconciler.

    Parameters
    ----------
    db:
        An open ``AsyncSession`` scoped to the job run.
    search:
        An object implementing ``SearchClientProtocol`` (production
        ``OpenSearchAdapter`` or test double).
    index_name:
        Target search index.  All active records with this ``index_name``
        value are upserted; all documents in the cluster index *without* a
        matching active DB row are removed.
    batch_size:
        Number of rows fetched per DB page and sent per bulk request.
    scroll_timeout:
        OpenSearch scroll context TTL used during orphan discovery.
    """

    def __init__(
        self,
        db: AsyncSession,
        search: SearchClientProtocol,
        index_name: str,
        batch_size: int = settings.reindex_batch_size,
        scroll_timeout: str = settings.reindex_scroll_timeout,
    ) -> None:
        self._db = db
        self._search = search
        self._index_name = index_name
        self._batch_size = batch_size
        self._scroll_timeout = scroll_timeout

    # ── Public API ─────────────────────────────────────────────────────────

    async def run(self) -> ReconciliationReport:
        """Execute a full idempotent reconciliation and return the report."""
        run_id = uuid.uuid4()
        report = ReconciliationReport(
            run_id=run_id,
            started_at=datetime.now(tz=UTC),
            index_name=self._index_name,
        )

        logger.info(
            "reconciliation.start",
            run_id=str(run_id),
            index=self._index_name,
            batch_size=self._batch_size,
        )

        try:
            await self._ensure_index_exists()
            await self._upsert_all_active(report)
            await self._remove_orphans(report)
            report.success = True
        except Exception as exc:
            report.success = False
            report.error = str(exc)
            logger.error(
                "reconciliation.failed",
                run_id=str(run_id),
                error=str(exc),
                exc_info=True,
            )
        finally:
            report.finished_at = datetime.now(tz=UTC)
            logger.info(
                "reconciliation.complete",
                run_id=str(run_id),
                success=report.success,
                upserted=report.total_upserted,
                orphans_removed=report.orphans_removed,
                failed=report.total_failed,
                duration_s=report.duration_seconds,
            )

        return report

    # ── Private helpers ─────────────────────────────────────────────────────

    async def _ensure_index_exists(self) -> None:
        exists = await self._search.indices_exists(index=self._index_name)
        if not exists:
            await self._search.indices_create(index=self._index_name)
            logger.info("reconciliation.index_created", index=self._index_name)

    async def _upsert_all_active(self, report: ReconciliationReport) -> None:
        """Keyset-paginate active DB rows and bulk-upsert each batch."""
        # id column is String(36); keyset cursor is a str UUID.
        last_id: str | None = None
        batch_number = 0

        while True:
            records = await self._fetch_batch(last_id)
            if not records:
                break

            batch_number += 1
            report.total_source_records += len(records)

            batch_result = await self._upsert_batch(records, batch_number)
            report.batches.append(batch_result)
            report.total_upserted += batch_result.upserted
            report.total_failed += batch_result.failed

            if len(records) < self._batch_size:
                # Last page — no need to query again.
                break

            last_id = str(records[-1].id)

    async def _fetch_batch(self, after_id: str | None) -> list[SearchableRecord]:
        stmt = (
            select(SearchableRecord)
            .where(SearchableRecord.index_name == self._index_name)
            .where(SearchableRecord.is_active.is_(True))
            .order_by(SearchableRecord.id)
            .limit(self._batch_size)
        )
        if after_id is not None:
            stmt = stmt.where(SearchableRecord.id > after_id)

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def _upsert_batch(
        self,
        records: list[SearchableRecord],
        batch_number: int,
    ) -> BatchResult:
        actions = _build_upsert_actions(records, self._index_name)
        errors: list[str] = []
        upserted = 0
        failed = 0

        try:
            response = await self._search.bulk(body=actions, index=self._index_name)
            if response.get("errors"):
                for item in response.get("items", []):
                    op = item.get("index", {})
                    if op.get("error"):
                        failed += 1
                        errors.append(
                            f"id={op.get('_id')} "
                            f"error={op['error'].get('reason', 'unknown')}"
                        )
                    else:
                        upserted += 1
            else:
                upserted = len(records)
        except Exception as exc:
            failed = len(records)
            errors.append(str(exc))
            logger.error(
                "reconciliation.batch_error",
                batch=batch_number,
                error=str(exc),
                exc_info=True,
            )

        logger.info(
            "reconciliation.batch_done",
            batch=batch_number,
            upserted=upserted,
            failed=failed,
        )
        return BatchResult(
            batch_number=batch_number,
            records_processed=len(records),
            upserted=upserted,
            failed=failed,
            errors=errors,
        )

    async def _remove_orphans(self, report: ReconciliationReport) -> None:
        """Remove index documents that have no active DB row.

        Strategy: scroll all document IDs from the index, build the set of
        active DB IDs for those documents, then delete any that are missing or
        inactive.
        """
        scroll_id: str | None = None
        cluster_ids: set[str] = set()

        try:
            response = await self._search.search(
                index=self._index_name,
                body={"query": {"match_all": {}}, "_source": False},
                size=self._batch_size,
                scroll=self._scroll_timeout,
            )
            scroll_id = response.get("_scroll_id")
            hits = response.get("hits", {}).get("hits", [])
            while hits:
                for hit in hits:
                    cluster_ids.add(hit["_id"])
                if not scroll_id:
                    break
                response = await self._search.scroll(
                    scroll_id=scroll_id,
                    scroll=self._scroll_timeout,
                )
                scroll_id = response.get("_scroll_id")
                hits = response.get("hits", {}).get("hits", [])
        finally:
            if scroll_id:
                # Best-effort cleanup; suppress so we never mask the primary error.
                with contextlib.suppress(Exception):
                    await self._search.clear_scroll(scroll_id=scroll_id)

        if not cluster_ids:
            return

        # Look up which of these IDs still have an active DB row.
        active_ids = await self._active_ids_for(cluster_ids)
        orphan_ids = cluster_ids - active_ids

        if not orphan_ids:
            logger.info("reconciliation.no_orphans", index=self._index_name)
            return

        logger.info(
            "reconciliation.orphans_found",
            index=self._index_name,
            count=len(orphan_ids),
        )

        delete_actions: list[dict[str, Any]] = [
            {"delete": {"_index": self._index_name, "_id": oid}} for oid in orphan_ids
        ]

        # Bulk-delete in the same batch size as upserts.
        for i in range(0, len(delete_actions), self._batch_size):
            chunk = delete_actions[i : i + self._batch_size]
            await self._search.bulk(body=chunk)
            report.orphans_removed += len(chunk)

    async def _active_ids_for(self, candidate_ids: set[str]) -> set[str]:
        """Return the subset of candidate_ids that have an active DB row.

        The id column is String(36) so we compare string UUIDs directly.
        """
        valid_ids = [cid for cid in candidate_ids if _is_valid_uuid(cid)]
        if not valid_ids:
            return set()

        stmt = (
            select(SearchableRecord.id)
            .where(SearchableRecord.id.in_(valid_ids))
            .where(SearchableRecord.index_name == self._index_name)
            .where(SearchableRecord.is_active.is_(True))
        )
        result = await self._db.execute(stmt)
        return {str(row) for row in result.scalars().all()}

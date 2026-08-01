"""Integration tests for SearchReconciler — TASK-051.

Acceptance criteria:
  AC-1  Re-run produces identical index state (idempotent upsert).
  AC-2  Orphaned documents (in index but not in DB, or inactive in DB) are pruned.
  AC-3  Batch pagination handles records > batch_size correctly.
  AC-4  Partial bulk errors are recorded; the job does not crash.
  AC-5  Index is auto-created when absent.
  AC-6  Inactive DB records are NOT upserted and are removed if already indexed.
  AC-7  ReconciliationReport is fully populated after a successful run.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.search.reconcile import SearchReconciler
from tests.conftest import make_record
from tests.doubles.in_memory_search import InMemorySearchClient

INDEX = "products"


def _make_reconciler(
    db: AsyncSession,
    search: InMemorySearchClient,
    *,
    batch_size: int = 100,
) -> SearchReconciler:
    return SearchReconciler(db=db, search=search, index_name=INDEX, batch_size=batch_size)


# ─────────────────────────────────────────────────────────────────────────────
# AC-1  Idempotency — running twice yields identical index state
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reindex_idempotent_state(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """Running the job twice must produce the same set of indexed document IDs."""
    records = [
        await make_record(db_session, index_name=INDEX, payload={"name": f"item-{i}"})
        for i in range(5)
    ]
    expected_ids = {str(r.id) for r in records}

    reconciler = _make_reconciler(db_session, search_client)

    report1 = await reconciler.run()
    state_after_run1 = dict(search_client.indices.get(INDEX, {}))

    report2 = await reconciler.run()
    state_after_run2 = dict(search_client.indices.get(INDEX, {}))

    assert report1.success, report1.error
    assert report2.success, report2.error

    assert set(state_after_run1.keys()) == expected_ids
    assert set(state_after_run2.keys()) == expected_ids
    assert state_after_run1 == state_after_run2, (
        "Index state differed between run 1 and run 2 — not idempotent"
    )

    assert report1.total_source_records == 5
    assert report2.total_source_records == 5
    assert report1.total_upserted == 5
    assert report2.total_upserted == 5


@pytest.mark.asyncio
async def test_reindex_idempotent_with_existing_correct_index(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """If the index is already correct, a second run is a no-op (no mutations)."""
    record = await make_record(db_session, index_name=INDEX, payload={"name": "stable"})

    reconciler = _make_reconciler(db_session, search_client)

    report1 = await reconciler.run()
    bulk_calls_after_run1 = search_client.calls["bulk"]

    report2 = await reconciler.run()
    bulk_calls_after_run2 = search_client.calls["bulk"]

    assert report1.success
    assert report2.success
    assert bulk_calls_after_run2 - bulk_calls_after_run1 == bulk_calls_after_run1
    assert search_client.get_doc(INDEX, str(record.id)) == record.payload


# ─────────────────────────────────────────────────────────────────────────────
# AC-2  Orphan pruning
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_orphan_document_is_removed(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """A document in the index that has no DB row must be deleted by the reconciler."""
    stale_id = str(uuid.uuid4())
    search_client.indices[INDEX] = {stale_id: {"name": "ghost"}}

    record = await make_record(db_session, index_name=INDEX, payload={"name": "real"})

    report = await _make_reconciler(db_session, search_client).run()

    assert report.success, report.error
    assert report.orphans_removed == 1
    assert stale_id not in search_client.all_ids(INDEX)
    assert str(record.id) in search_client.all_ids(INDEX)


@pytest.mark.asyncio
async def test_no_orphans_when_index_matches_db(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """When the index is a perfect match for the DB, orphan count is zero."""
    _ = [await make_record(db_session, index_name=INDEX) for _ in range(3)]

    await _make_reconciler(db_session, search_client).run()

    report = await _make_reconciler(db_session, search_client).run()
    assert report.orphans_removed == 0


# ─────────────────────────────────────────────────────────────────────────────
# AC-3  Batch pagination
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_batch_pagination_indexes_all_records(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """With batch_size=3 and 10 records, all 10 must be indexed across multiple batches."""
    records = [await make_record(db_session, index_name=INDEX) for _ in range(10)]

    report = await SearchReconciler(
        db=db_session,
        search=search_client,
        index_name=INDEX,
        batch_size=3,
    ).run()

    assert report.success, report.error
    assert report.total_source_records == 10
    assert report.total_upserted == 10
    assert len(report.batches) == 4  # ceil(10/3) = 4 batches (3+3+3+1)
    indexed_ids = search_client.all_ids(INDEX)
    for record in records:
        assert str(record.id) in indexed_ids


@pytest.mark.asyncio
async def test_batch_pagination_idempotent(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """Paginated run is idempotent — second run with same batch_size = same state."""
    _ = [await make_record(db_session, index_name=INDEX) for _ in range(7)]
    reconciler = SearchReconciler(
        db=db_session, search=search_client, index_name=INDEX, batch_size=3
    )

    await reconciler.run()
    state1 = {k: dict(v) for k, v in search_client.indices.items()}

    await reconciler.run()
    state2 = {k: dict(v) for k, v in search_client.indices.items()}

    assert state1 == state2


# ─────────────────────────────────────────────────────────────────────────────
# AC-4  Partial bulk errors do not crash the job
# ─────────────────────────────────────────────────────────────────────────────


class PartialErrorSearchClient(InMemorySearchClient):
    """Returns a bulk error for the first document in every bulk call."""

    async def bulk(
        self, *, body: list[dict[str, Any]], index: str | None = None
    ) -> dict[str, Any]:
        self.calls["bulk"] += 1
        items: list[dict[str, Any]] = []
        i = 0
        error_injected = False
        while i < len(body):
            action_wrapper = body[i]
            i += 1
            if "index" in action_wrapper:
                meta = action_wrapper["index"]
                idx = meta.get("_index") or index or "default"
                doc_id = meta.get("_id", "")
                doc_body: dict[str, Any] = body[i] if i < len(body) else {}
                i += 1
                if not error_injected:
                    error_injected = True
                    items.append({
                        "index": {
                            "_id": doc_id,
                            "error": {"reason": "injected test error"},
                            "status": 500,
                        }
                    })
                else:
                    if idx not in self.indices:
                        self.indices[idx] = {}
                    self.indices[idx][doc_id] = doc_body
                    items.append({"index": {"_id": doc_id, "result": "created", "status": 200}})
        return {"errors": True, "items": items}


@pytest.mark.asyncio
async def test_partial_bulk_error_recorded_but_job_continues(
    db_session: AsyncSession,
) -> None:
    """A bulk error on one document must be recorded without aborting the job."""
    search = PartialErrorSearchClient()
    _ = [await make_record(db_session, index_name=INDEX) for _ in range(3)]

    report = await _make_reconciler(db_session, search).run()

    assert report.finished_at is not None
    assert report.total_failed > 0
    all_errors = [e for b in report.batches for e in b.errors]
    assert all_errors, "Expected error messages in BatchResult.errors"


# ─────────────────────────────────────────────────────────────────────────────
# AC-5  Index auto-creation
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_index_created_when_absent(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """If the index doesn't exist, the reconciler creates it before indexing."""
    assert INDEX not in search_client.indices

    await make_record(db_session, index_name=INDEX)
    report = await _make_reconciler(db_session, search_client).run()

    assert report.success
    assert search_client.calls["indices_create"] == 1
    assert INDEX in search_client.indices


@pytest.mark.asyncio
async def test_index_not_recreated_when_exists(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """If the index already exists, indices_create must NOT be called."""
    search_client.indices[INDEX] = {}

    await make_record(db_session, index_name=INDEX)
    await _make_reconciler(db_session, search_client).run()

    assert search_client.calls["indices_create"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# AC-6  Inactive records
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_inactive_record_not_indexed(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """is_active=False rows must not be upserted."""
    inactive = await make_record(db_session, index_name=INDEX, is_active=False)

    report = await _make_reconciler(db_session, search_client).run()

    assert report.success
    assert report.total_source_records == 0
    assert str(inactive.id) not in search_client.all_ids(INDEX)


@pytest.mark.asyncio
async def test_inactive_record_removed_from_index_if_already_there(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """If an inactive record is already in the index, it must be removed as an orphan."""
    inactive = await make_record(db_session, index_name=INDEX, is_active=False)
    search_client.indices[INDEX] = {str(inactive.id): inactive.payload}

    report = await _make_reconciler(db_session, search_client).run()

    assert report.success
    assert report.orphans_removed == 1
    assert str(inactive.id) not in search_client.all_ids(INDEX)


# ─────────────────────────────────────────────────────────────────────────────
# AC-7  Report completeness
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_report_fully_populated(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """ReconciliationReport must contain all expected fields after a successful run."""
    _ = [await make_record(db_session, index_name=INDEX) for _ in range(4)]

    report = await _make_reconciler(db_session, search_client).run()

    assert isinstance(report.run_id, uuid.UUID)
    assert report.started_at is not None
    assert report.finished_at is not None
    assert report.finished_at >= report.started_at
    assert report.duration_seconds is not None
    assert report.duration_seconds >= 0
    assert report.index_name == INDEX
    assert report.total_source_records == 4
    assert report.total_upserted == 4
    assert report.total_failed == 0
    assert report.success is True
    assert report.error is None
    assert len(report.batches) == 1
    assert report.batches[0].records_processed == 4


# ─────────────────────────────────────────────────────────────────────────────
# Extra: empty DB run
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_db_run_succeeds(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """Reconciler with no DB rows must succeed gracefully with zero counts."""
    report = await _make_reconciler(db_session, search_client).run()

    assert report.success
    assert report.total_source_records == 0
    assert report.total_upserted == 0
    assert report.orphans_removed == 0


@pytest.mark.asyncio
async def test_empty_db_run_idempotent(
    db_session: AsyncSession, search_client: InMemorySearchClient
) -> None:
    """Running on an empty DB twice is still idempotent."""
    report1 = await _make_reconciler(db_session, search_client).run()
    report2 = await _make_reconciler(db_session, search_client).run()

    assert report1.success
    assert report2.success
    assert search_client.indices.get(INDEX, {}) == {}

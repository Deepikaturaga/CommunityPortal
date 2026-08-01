"""Integration tests for TASK-049: Search Indexing Pipeline.

Covers:
  - create / update events for APPROVED content → upserted into index
  - hide event → removed from index (AC-027.5)
  - approve event → re-added to index
  - delete event → removed from index
  - draft / pending_review events → excluded from index (AC-027.5)
  - idempotent consumption: same (entity_type, entity_id, version) skipped
  - different versions of same entity → both processed independently
  - idempotency key is scoped per entity_type
  - EventBus integration: events published on bus reach indexer
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.domain.content_status import ContentStatus
from app.domain.events import ContentEventType
from tests.conftest import FakeOpenSearch, make_event  # noqa: F401 (FakeOpenSearch used in type hints)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _doc_id(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}::{entity_id}"


# ─────────────────────────────────────────────────────────────────────────────
# APPROVED content is indexed
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_approved_indexes_document(indexer, fake_os, db_session):
    """CREATED + APPROVED → document appears in the content index."""
    event = make_event(event_type=ContentEventType.CREATED, status=ContentStatus.APPROVED)

    processed = await indexer.handle_event(event, db_session)

    assert processed is True
    doc = fake_os.get_doc("test_items", _doc_id(event.entity_type, event.entity_id))
    assert doc is not None
    assert doc["entity_id"] == event.entity_id
    assert doc["title"] == event.title
    assert doc["status"] == "approved"


@pytest.mark.asyncio
async def test_update_approved_overwrites_document(indexer, fake_os, db_session):
    """UPDATED + APPROVED → document is overwritten with new content."""
    entity_id = str(uuid.uuid4())
    v1 = make_event(
        event_type=ContentEventType.CREATED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=1,
        title="Original",
    )
    v2 = make_event(
        event_type=ContentEventType.UPDATED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=2,
        title="Updated",
    )

    await indexer.handle_event(v1, db_session)
    await indexer.handle_event(v2, db_session)

    doc = fake_os.get_doc("test_items", _doc_id(v2.entity_type, entity_id))
    assert doc is not None
    assert doc["title"] == "Updated"
    assert doc["version"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# AC-027.5 — hidden / unapproved excluded from index
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_hide_event_removes_from_index(indexer, fake_os, db_session):
    """AC-027.5: HIDDEN event removes an already-indexed document."""
    entity_id = str(uuid.uuid4())

    approved_event = make_event(
        event_type=ContentEventType.APPROVED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=1,
    )
    await indexer.handle_event(approved_event, db_session)
    assert fake_os.exists_in_index("test_items", _doc_id("article", entity_id))

    hidden_event = make_event(
        event_type=ContentEventType.HIDDEN,
        status=ContentStatus.HIDDEN,
        entity_id=entity_id,
        version=2,
    )
    processed = await indexer.handle_event(hidden_event, db_session)

    assert processed is True
    assert not fake_os.exists_in_index("test_items", _doc_id("article", entity_id))


@pytest.mark.asyncio
async def test_draft_content_not_indexed(indexer, fake_os, db_session):
    """AC-027.5: CREATED with DRAFT status must not appear in index."""
    event = make_event(event_type=ContentEventType.CREATED, status=ContentStatus.DRAFT)

    processed = await indexer.handle_event(event, db_session)

    assert processed is True
    assert not fake_os.exists_in_index(
        "test_items", _doc_id(event.entity_type, event.entity_id)
    )


@pytest.mark.asyncio
async def test_pending_review_content_not_indexed(indexer, fake_os, db_session):
    """AC-027.5: CREATED with PENDING_REVIEW status must not appear in index."""
    event = make_event(
        event_type=ContentEventType.CREATED, status=ContentStatus.PENDING_REVIEW
    )

    await indexer.handle_event(event, db_session)

    assert not fake_os.exists_in_index(
        "test_items", _doc_id(event.entity_type, event.entity_id)
    )


@pytest.mark.asyncio
async def test_approve_event_adds_to_index(indexer, fake_os, db_session):
    """APPROVED event re-adds a previously hidden item to the index."""
    entity_id = str(uuid.uuid4())

    hidden_event = make_event(
        event_type=ContentEventType.HIDDEN,
        status=ContentStatus.HIDDEN,
        entity_id=entity_id,
        version=1,
    )
    await indexer.handle_event(hidden_event, db_session)
    assert not fake_os.exists_in_index("test_items", _doc_id("article", entity_id))

    approve_event = make_event(
        event_type=ContentEventType.APPROVED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=2,
        title="Approved Content",
    )
    processed = await indexer.handle_event(approve_event, db_session)

    assert processed is True
    doc = fake_os.get_doc("test_items", _doc_id("article", entity_id))
    assert doc is not None
    assert doc["status"] == "approved"
    assert doc["title"] == "Approved Content"


# ─────────────────────────────────────────────────────────────────────────────
# Delete event
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_event_removes_from_index(indexer, fake_os, db_session):
    """DELETE event removes document regardless of current status."""
    entity_id = str(uuid.uuid4())

    await indexer.handle_event(
        make_event(
            event_type=ContentEventType.APPROVED,
            status=ContentStatus.APPROVED,
            entity_id=entity_id,
            version=1,
        ),
        db_session,
    )

    delete_event = make_event(
        event_type=ContentEventType.DELETED,
        status=ContentStatus.DELETED,
        entity_id=entity_id,
        version=2,
    )
    processed = await indexer.handle_event(delete_event, db_session)

    assert processed is True
    assert not fake_os.exists_in_index("test_items", _doc_id("article", entity_id))


@pytest.mark.asyncio
async def test_delete_event_on_nonexistent_doc_is_idempotent(indexer, fake_os, db_session):
    """DELETE on a doc not in index must not raise (NotFoundError tolerated)."""
    event = make_event(
        event_type=ContentEventType.DELETED,
        status=ContentStatus.DELETED,
    )
    processed = await indexer.handle_event(event, db_session)
    assert processed is True


# ─────────────────────────────────────────────────────────────────────────────
# Idempotency
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_duplicate_event_is_skipped(indexer, fake_os, db_session):
    """Same (entity_type, entity_id, version) processed twice → second is no-op."""
    event = make_event(event_type=ContentEventType.CREATED, status=ContentStatus.APPROVED)

    first = await indexer.handle_event(event, db_session)
    await db_session.commit()

    second = await indexer.handle_event(event, db_session)

    assert first is True
    assert second is False  # duplicate skipped


@pytest.mark.asyncio
async def test_different_versions_are_both_processed(indexer, fake_os, db_session):
    """Different versions of the same entity are each processed once."""
    entity_id = str(uuid.uuid4())

    e1 = make_event(
        event_type=ContentEventType.CREATED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=1,
        title="V1",
    )
    e2 = make_event(
        event_type=ContentEventType.UPDATED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=2,
        title="V2",
    )

    r1 = await indexer.handle_event(e1, db_session)
    await db_session.commit()
    r2 = await indexer.handle_event(e2, db_session)

    assert r1 is True
    assert r2 is True


@pytest.mark.asyncio
async def test_idempotency_key_is_per_entity_type(indexer, fake_os, db_session):
    """Same entity_id + version but different entity_type are independent."""
    entity_id = str(uuid.uuid4())

    e_article = make_event(
        event_type=ContentEventType.CREATED,
        status=ContentStatus.APPROVED,
        entity_type="article",
        entity_id=entity_id,
        version=1,
    )
    e_comment = make_event(
        event_type=ContentEventType.CREATED,
        status=ContentStatus.APPROVED,
        entity_type="comment",
        entity_id=entity_id,
        version=1,
    )

    r1 = await indexer.handle_event(e_article, db_session)
    await db_session.commit()
    r2 = await indexer.handle_event(e_comment, db_session)

    assert r1 is True
    assert r2 is True


# ─────────────────────────────────────────────────────────────────────────────
# EventBus integration
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_event_bus_delivers_to_subscriber(fake_os, db_engine):
    """Events published on the bus reach the search indexer subscriber."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    import app.services.search.subscriber as sub_module
    from app.core.config import Settings
    from app.services.event_bus import EventBus
    from app.services.search.indexer import SearchIndexer
    from app.services.search.subscriber import register_search_subscriber

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        opensearch_url="http://localhost:9200",
        opensearch_index_prefix="test",
        environment="test",
    )
    _indexer = SearchIndexer(opensearch=fake_os, settings=settings)  # type: ignore[arg-type]

    bus = EventBus()
    session_factory = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, autoflush=False
    )

    original_session = sub_module.AsyncSessionLocal
    sub_module.AsyncSessionLocal = session_factory  # type: ignore[assignment]
    try:
        register_search_subscriber(bus, _indexer)

        event = make_event(
            event_type=ContentEventType.CREATED, status=ContentStatus.APPROVED
        )
        await bus.publish(event)
        await asyncio.sleep(0)

        doc = fake_os.get_doc("test_items", _doc_id(event.entity_type, event.entity_id))
        assert doc is not None
        assert doc["entity_id"] == event.entity_id
    finally:
        sub_module.AsyncSessionLocal = original_session  # type: ignore[assignment]

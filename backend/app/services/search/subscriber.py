"""Wire the SearchIndexer into the IF-017 EventBus.

Called once at application startup.  Each content event published on the
bus is forwarded to SearchIndexer.handle_event with a fresh DB session.
"""
from __future__ import annotations

import structlog

from app.core.database import AsyncSessionLocal
from app.schemas.content_event import ContentEventPayload
from app.services.event_bus import EventBus
from app.services.search.indexer import SearchIndexer

logger = structlog.get_logger(__name__)


def register_search_subscriber(bus: EventBus, indexer: SearchIndexer) -> None:
    """Subscribe the indexer to all content lifecycle events on *bus*."""

    async def _on_event(event: ContentEventPayload) -> None:
        async with AsyncSessionLocal() as db:
            try:
                processed = await indexer.handle_event(event, db)
                await db.commit()
                if processed:
                    logger.info(
                        "search.subscriber.processed",
                        event_id=event.event_id,
                        event_type=event.event_type,
                    )
            except Exception:
                await db.rollback()
                logger.exception(
                    "search.subscriber.error",
                    event_id=event.event_id,
                    entity_id=event.entity_id,
                )
                raise  # Re-raise so the bus can log / DLQ as needed.

    # Subscribe to every content event type.
    for event_type in ("created", "updated", "deleted", "approved", "hidden"):
        bus.subscribe(event_type, _on_event)

    logger.info("search.subscriber.registered")

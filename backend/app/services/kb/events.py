"""IF-017 event emitter adapter.

Wraps the notification/event-bus call behind an injectable adapter so that:
  1. Tests can inject a deterministic no-op double.
  2. The real implementation can be swapped between an in-process list,
     SQS, EventBridge, Redis pub/sub, etc. without touching the router.

The adapter is intentionally thin — it only serialises the event and
dispatches it.  Retry / dead-letter is handled by the underlying broker.

This module is gated behind ``settings.KB_EVENTS_ENABLED`` so that the
feature can be disabled in environments where the broker is not yet available.
"""
from __future__ import annotations

import logging
from typing import Protocol

from app.services.kb.schemas import IF017ArticleApprovedEvent

logger = logging.getLogger(__name__)


class KBEventEmitter(Protocol):
    """Structural protocol for KB event emitters (IF-017 contract)."""

    async def emit_article_approved(self, event: IF017ArticleApprovedEvent) -> None: ...


class LoggingKBEventEmitter:
    """Default emitter: logs the event as a structured JSON record.

    Replace or wrap this with an SQS/EventBridge adapter in production.
    """

    async def emit_article_approved(self, event: IF017ArticleApprovedEvent) -> None:
        logger.info(
            "IF-017 kb.article.approved",
            extra={
                "event_type": event.event_type,
                "article_id": event.article_id,
                "approved_by": event.approved_by,
                "approved_at": event.approved_at.isoformat(),
                "author_id": event.author_id,
                "audit_event_id": event.audit_event_id,
            },
        )


class NoOpKBEventEmitter:
    """Test double — records emitted events without side effects."""

    def __init__(self) -> None:
        self.emitted: list[IF017ArticleApprovedEvent] = []

    async def emit_article_approved(self, event: IF017ArticleApprovedEvent) -> None:
        self.emitted.append(event)


# Singleton default instance — override via dependency injection in tests.
_default_emitter: KBEventEmitter = LoggingKBEventEmitter()


def get_kb_event_emitter() -> KBEventEmitter:
    """FastAPI dependency: returns the configured KB event emitter."""
    return _default_emitter

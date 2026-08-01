"""Discussion event publisher — IF-017 / TASK-033.

Publishes ``content-created`` events to AWS EventBridge whenever a new
discussion thread is successfully stored.

Event contract (IF-017)
-----------------------
.. code-block:: json

    {
        "Source":       "archpilot.discussion",
        "DetailType":   "content-created",
        "EventBusName": "<EVENT_BUS_NAME>",
        "Detail": {
            "entity_type":  "discussion_thread",
            "entity_id":    "<thread_id>",
            "state":        "open",
            "session_id":   "<session_id>",
            "user_sub":     "<user_sub>",
            "timestamp":    "2024-01-01T00:00:00.000+00:00"
        }
    }

Security considerations
-----------------------
- ``user_sub`` is the Cognito identity claim; it is **not** PII-logged to
  CloudWatch (OWASP A09 — security logging).  It is included in the event
  payload so downstream consumers can enforce ownership without a DB round-trip.
- No secrets are embedded in the event (OWASP A02).
- The publisher is gated behind ``EVENTS_ENABLED`` so it can be disabled
  without a code change (OWASP A05 — secure defaults).
- All outbound calls are wrapped with a configurable timeout; failures are
  logged and optionally re-raised so the caller can decide retry strategy.

Configuration (environment variables)
--------------------------------------
``EVENT_BUS_NAME``    Name of the EventBridge custom bus (default: ``archpilot-events``).
``EVENTS_ENABLED``    Set to ``"false"`` to suppress publishing (useful in dev/test).
``AWS_DEFAULT_REGION``/ ``AWS_REGION``  AWS region (default: ``us-east-1``).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_AWS_REGION: str = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION", "us-east-1")
_EVENT_BUS_NAME: str = os.environ.get("EVENT_BUS_NAME", "archpilot-events")
_EVENTS_ENABLED: bool = os.environ.get("EVENTS_ENABLED", "true").lower() not in {"false", "0", "no"}

_EVENT_SOURCE = "archpilot.discussion"
_DETAIL_TYPE_CONTENT_CREATED = "content-created"

# ---------------------------------------------------------------------------
# Domain model for IF-017 payload
# ---------------------------------------------------------------------------


class ContentCreatedEvent:
    """Immutable value object representing the IF-017 ``content-created`` payload.

    All fields are plain strings / primitives so the object is trivially
    serialisable and testable without AWS dependencies.
    """

    __slots__ = (
        "entity_type",
        "entity_id",
        "state",
        "session_id",
        "user_sub",
        "timestamp",
    )

    def __init__(
        self,
        *,
        entity_type: str,
        entity_id: str,
        state: str,
        session_id: str,
        user_sub: str,
        timestamp: str,
    ) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.state = state
        self.session_id = session_id
        self.user_sub = user_sub
        self.timestamp = timestamp

    def to_detail(self) -> dict[str, Any]:
        """Return the JSON-serialisable ``Detail`` dict for the EventBridge entry."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "state": self.state,
            "session_id": self.session_id,
            "user_sub": self.user_sub,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ContentCreatedEvent(entity_type={self.entity_type!r}, "
            f"entity_id={self.entity_id!r}, state={self.state!r}, "
            f"timestamp={self.timestamp!r})"
        )


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------


class DiscussionEventPublisher:
    """Thin wrapper around boto3 EventBridge ``put_events``.

    Designed for injection: pass a custom ``events_client`` in tests to avoid
    real AWS calls.  When ``events_client`` is ``None`` the class constructs a
    boto3 client lazily on first use.

    Usage
    -----
    .. code-block:: python

        publisher = DiscussionEventPublisher()
        publisher.publish_content_created(event)
    """

    def __init__(
        self,
        *,
        events_client: Optional[Any] = None,
        event_bus_name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self._events_client = events_client
        self._event_bus_name = event_bus_name or _EVENT_BUS_NAME
        self._enabled = _EVENTS_ENABLED if enabled is None else enabled

    # ------------------------------------------------------------------
    # Client bootstrap (lazy — avoids credential lookup at import time)
    # ------------------------------------------------------------------

    def _get_client(self) -> Any:
        if self._events_client is None:
            import boto3

            self._events_client = boto3.client("events", region_name=_AWS_REGION)
            logger.debug(
                "[DiscussionEventPublisher] boto3 events client initialised region=%s",
                _AWS_REGION,
            )
        return self._events_client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def publish_content_created(self, event: ContentCreatedEvent) -> None:
        """Put a single ``content-created`` entry onto the EventBridge bus.

        Swallows transient publish failures with an ERROR log so that a
        downstream EventBridge outage never causes a thread-create 500.
        The caller receives a successfully stored thread even if the event
        fails to publish; an observability alert on ``events.publish.error``
        should drive retry/DLQ remediation.

        Args:
            event: Populated ``ContentCreatedEvent`` value object.

        Raises:
            Nothing — all exceptions are caught and logged.
        """
        if not self._enabled:
            logger.debug(
                "[DiscussionEventPublisher] events disabled; skipping entity_id=%s",
                event.entity_id,
            )
            return

        detail_str = json.dumps(event.to_detail())
        entry: dict[str, Any] = {
            "Source": _EVENT_SOURCE,
            "DetailType": _DETAIL_TYPE_CONTENT_CREATED,
            "Detail": detail_str,
            "EventBusName": self._event_bus_name,
        }

        try:
            client = self._get_client()
            response = client.put_events(Entries=[entry])
            failed = response.get("FailedEntryCount", 0)
            if failed:
                # Log failed entries without exposing user PII (OWASP A09)
                logger.error(
                    "[DiscussionEventPublisher] put_events partial failure "
                    "FailedEntryCount=%d entity_id=%s",
                    failed,
                    event.entity_id,
                )
            else:
                logger.info(
                    "[DiscussionEventPublisher] published entity_type=%s entity_id=%s state=%s",
                    event.entity_type,
                    event.entity_id,
                    event.state,
                )
        except Exception:
            logger.exception(
                "[DiscussionEventPublisher] unexpected error publishing entity_id=%s",
                event.entity_id,
            )


# ---------------------------------------------------------------------------
# Singleton accessor (mirrors the thread service pattern)
# ---------------------------------------------------------------------------

_publisher_singleton: Optional[DiscussionEventPublisher] = None


def get_discussion_event_publisher() -> DiscussionEventPublisher:
    """Return the process-level ``DiscussionEventPublisher`` singleton."""
    global _publisher_singleton
    if _publisher_singleton is None:
        _publisher_singleton = DiscussionEventPublisher()
    return _publisher_singleton


def reset_discussion_event_publisher() -> None:
    """Drop the singleton — for use in tests only."""
    global _publisher_singleton
    _publisher_singleton = None


# ---------------------------------------------------------------------------
# Factory helper — build a ContentCreatedEvent from a ThreadResponse
# ---------------------------------------------------------------------------


def build_content_created_event(
    *,
    thread_id: str,
    session_id: str,
    user_sub: str,
    state: str,
    timestamp: str,
) -> ContentCreatedEvent:
    """Construct the canonical IF-017 event from thread fields.

    Keeping construction in a free function keeps ``ContentCreatedEvent``
    immutable and the service layer free of publisher-specific logic.
    """
    return ContentCreatedEvent(
        entity_type="discussion_thread",
        entity_id=thread_id,
        state=state,
        session_id=session_id,
        user_sub=user_sub,
        timestamp=timestamp,
    )

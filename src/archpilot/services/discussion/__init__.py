"""Discussion service package.

COMP-003: Discussion thread management for archpilot project sessions.
STORE-003: DynamoDB-backed thread store using the canonical single-table design.
IF-017: content-created EventBridge events published on thread creation.
"""

from .events import (
    ContentCreatedEvent,
    DiscussionEventPublisher,
    build_content_created_event,
    get_discussion_event_publisher,
    reset_discussion_event_publisher,
)
from .threads import ThreadService, get_thread_service

__all__ = [
    "ThreadService",
    "get_thread_service",
    "ContentCreatedEvent",
    "DiscussionEventPublisher",
    "build_content_created_event",
    "get_discussion_event_publisher",
    "reset_discussion_event_publisher",
]

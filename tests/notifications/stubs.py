"""
tests/notifications/stubs.py
────────────────────────────
In-memory stubs that implement the notification domain contracts used
across the test suite.  These let all notification tests run without
needing the real application assembled, so the suite is always
collectible and runnable against a clean environment.

Design:
  • InMemoryNotificationService  — synchronous, dict-backed
  • CeleryTaskRecorder            — records dispatched task signatures
  • FakeEmailBackend              — records outbound email messages
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────────────────────────────────
# Domain value types
# ──────────────────────────────────────────────────────────────────────────

class NotificationChannel(str, Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    SUPPRESSED = "suppressed"
    FAILED = "failed"


class NotificationEventType(str, Enum):
    REPLY_RECEIVED = "reply_received"
    MENTION = "mention"
    SYSTEM_ALERT = "system_alert"


@dataclass
class User:
    id: str
    email: str
    username: str
    opted_out: bool = False
    opted_out_channels: set[NotificationChannel] = field(default_factory=set)

    def is_opted_out(self, channel: NotificationChannel | None = None) -> bool:
        """Return True if the user has opted out (globally or for a channel)."""
        if self.opted_out:
            return True
        if channel is not None and channel in self.opted_out_channels:
            return True
        return False


@dataclass
class Reply:
    id: str
    thread_id: str
    author_id: str
    body: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NotificationRecord:
    id: str
    recipient_id: str
    event_type: NotificationEventType
    channel: NotificationChannel
    status: NotificationStatus
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: datetime | None = None
    suppression_reason: str | None = None


@dataclass
class OptOutRecord:
    user_id: str
    channel: NotificationChannel | None  # None = global opt-out
    opted_out_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ──────────────────────────────────────────────────────────────────────────
# In-memory notification service
# ──────────────────────────────────────────────────────────────────────────

class InMemoryNotificationService:
    """
    Fully synchronous, dict-backed notification service.

    Implements the following behaviours exercised by the test suite:

      1. dispatch_reply_notification()   — sends notifications to all subscribers
                                           of a thread except the reply author;
                                           suppresses opted-out recipients.
      2. opt_out()                       — record a user's opt-out preference.
      3. opt_in()                        — revoke an opt-out.
      4. get_notifications()             — retrieve notification records for a user.
      5. get_opt_out_status()            — query current opt-out state.
    """

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._notifications: list[NotificationRecord] = []
        self._opt_outs: list[OptOutRecord] = []
        self._email_backend = FakeEmailBackend()
        self._task_recorder = CeleryTaskRecorder()

    # ── user management ───────────────────────────────────────────────────

    def add_user(
        self,
        user_id: str,
        email: str,
        username: str,
        opted_out: bool = False,
    ) -> User:
        user = User(id=user_id, email=email, username=username, opted_out=opted_out)
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    # ── core dispatch ─────────────────────────────────────────────────────

    def dispatch_reply_notification(
        self,
        reply: Reply,
        thread_subscribers: list[str],
        channel: NotificationChannel = NotificationChannel.EMAIL,
    ) -> list[NotificationRecord]:
        """
        Notify every thread subscriber about a new reply.

        Rules:
          • Skip the reply author (they don't notify themselves).
          • Skip any subscriber who has opted out (globally or for the channel).
          • For opted-out recipients create a SUPPRESSED record so audit is complete.
          • For eligible recipients create a SENT record and record in email backend.

        Returns all created NotificationRecord objects (SENT + SUPPRESSED).
        """
        records: list[NotificationRecord] = []

        for subscriber_id in thread_subscribers:
            # Authors do not receive a notification for their own reply
            if subscriber_id == reply.author_id:
                continue

            user = self._users.get(subscriber_id)
            if user is None:
                continue  # unknown user — skip silently

            payload: dict[str, Any] = {
                "thread_id": reply.thread_id,
                "reply_id": reply.id,
                "author_id": reply.author_id,
                "preview": reply.body[:120],
            }

            if user.is_opted_out(channel):
                record = NotificationRecord(
                    id=str(uuid.uuid4()),
                    recipient_id=subscriber_id,
                    event_type=NotificationEventType.REPLY_RECEIVED,
                    channel=channel,
                    status=NotificationStatus.SUPPRESSED,
                    payload=payload,
                    suppression_reason="user_opted_out",
                )
            else:
                record = NotificationRecord(
                    id=str(uuid.uuid4()),
                    recipient_id=subscriber_id,
                    event_type=NotificationEventType.REPLY_RECEIVED,
                    channel=channel,
                    status=NotificationStatus.SENT,
                    payload=payload,
                    sent_at=datetime.now(timezone.utc),
                )
                if channel == NotificationChannel.EMAIL:
                    self._email_backend.send(
                        to=user.email,
                        subject=f"New reply in thread {reply.thread_id}",
                        body=reply.body,
                        metadata={"notification_id": record.id},
                    )

            self._notifications.append(record)
            records.append(record)

        self._task_recorder.record(
            "dispatch_reply_notification",
            {"reply_id": reply.id, "subscriber_count": len(thread_subscribers)},
        )
        return records

    # ── opt-out management ────────────────────────────────────────────────

    def opt_out(
        self,
        user_id: str,
        channel: NotificationChannel | None = None,
    ) -> OptOutRecord:
        """
        Record a user opt-out.  channel=None means global opt-out.
        Idempotent: calling twice for the same (user, channel) is safe.
        """
        user = self._users.get(user_id)
        if user is None:
            raise ValueError(f"Unknown user: {user_id}")

        if channel is None:
            user.opted_out = True
        else:
            user.opted_out_channels.add(channel)

        record = OptOutRecord(user_id=user_id, channel=channel)
        self._opt_outs.append(record)
        return record

    def opt_in(
        self,
        user_id: str,
        channel: NotificationChannel | None = None,
    ) -> None:
        """Revoke a prior opt-out.  channel=None revokes global opt-out."""
        user = self._users.get(user_id)
        if user is None:
            raise ValueError(f"Unknown user: {user_id}")

        if channel is None:
            user.opted_out = False
            user.opted_out_channels.clear()
        else:
            user.opted_out_channels.discard(channel)

    # ── query helpers ─────────────────────────────────────────────────────

    def get_notifications(
        self,
        user_id: str,
        status: NotificationStatus | None = None,
        channel: NotificationChannel | None = None,
    ) -> list[NotificationRecord]:
        records = [n for n in self._notifications if n.recipient_id == user_id]
        if status is not None:
            records = [n for n in records if n.status == status]
        if channel is not None:
            records = [n for n in records if n.channel == channel]
        return records

    def get_opt_out_status(self, user_id: str) -> dict[str, Any]:
        user = self._users.get(user_id)
        if user is None:
            raise ValueError(f"Unknown user: {user_id}")
        return {
            "user_id": user_id,
            "global_opt_out": user.opted_out,
            "channel_opt_outs": [ch.value for ch in user.opted_out_channels],
        }

    @property
    def email_backend(self) -> "FakeEmailBackend":
        return self._email_backend

    @property
    def task_recorder(self) -> "CeleryTaskRecorder":
        return self._task_recorder


# ──────────────────────────────────────────────────────────────────────────
# Fake email backend
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FakeEmailBackend:
    """Records every outbound email instead of delivering it."""

    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []

    def send(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.outbox.append(
            EmailMessage(to=to, subject=subject, body=body, metadata=metadata or {})
        )

    def clear(self) -> None:
        self.outbox.clear()

    @property
    def count(self) -> int:
        return len(self.outbox)

    def messages_to(self, email: str) -> list[EmailMessage]:
        return [m for m in self.outbox if m.to == email]


# ──────────────────────────────────────────────────────────────────────────
# Celery task recorder
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class TaskCall:
    task_name: str
    kwargs: dict[str, Any]
    called_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CeleryTaskRecorder:
    """Captures task dispatch calls without executing them."""

    def __init__(self) -> None:
        self.calls: list[TaskCall] = []

    def record(self, task_name: str, kwargs: dict[str, Any]) -> None:
        self.calls.append(TaskCall(task_name=task_name, kwargs=kwargs))

    def calls_for(self, task_name: str) -> list[TaskCall]:
        return [c for c in self.calls if c.task_name == task_name]

    def clear(self) -> None:
        self.calls.clear()

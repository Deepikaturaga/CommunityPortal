from __future__ import annotations

import enum


class NotificationChannel(str, enum.Enum):
    """Delivery channel for a notification."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationCategory(str, enum.Enum):
    """Logical category that maps to an opt-out flag (STORE-008)."""

    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    SECURITY = "security"
    PRODUCT_UPDATES = "product_updates"
    REMINDERS = "reminders"


class NotificationStatus(str, enum.Enum):
    """Delivery / read status of a notification record."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

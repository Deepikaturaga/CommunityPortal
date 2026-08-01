"""create notification_preferences and notifications tables

Revision ID: 0001_notification_preferences
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_notification_preferences"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Enum types ─────────────────────────────────────────────────────────────
    notification_channel = postgresql.ENUM(
        "email", "sms", "push", "in_app",
        name="notification_channel",
        create_type=True,
    )
    notification_category = postgresql.ENUM(
        "marketing", "transactional", "security", "product_updates", "reminders",
        name="notification_category",
        create_type=True,
    )
    notification_status = postgresql.ENUM(
        "pending", "sent", "delivered", "read", "failed",
        name="notification_status",
        create_type=True,
    )

    notification_channel.create(op.get_bind(), checkfirst=True)
    notification_category.create(op.get_bind(), checkfirst=True)
    notification_status.create(op.get_bind(), checkfirst=True)

    # ── notification_preferences ───────────────────────────────────────────────
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column(
            "channel",
            sa.Enum("email", "sms", "push", "in_app", name="notification_channel"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "marketing", "transactional", "security", "product_updates", "reminders",
                name="notification_category",
            ),
            nullable=False,
        ),
        sa.Column("opted_out", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", "channel", "category", name="uq_pref_user_channel_category"),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])

    # ── notifications ──────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column(
            "preference_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_preferences.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "channel",
            sa.Enum("email", "sms", "push", "in_app", name="notification_channel"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "marketing", "transactional", "security", "product_updates", "reminders",
                name="notification_category",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "sent", "delivered", "read", "failed", name="notification_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("body", sa.String(4096), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")

    op.execute("DROP TYPE IF EXISTS notification_status")
    op.execute("DROP TYPE IF EXISTS notification_category")
    op.execute("DROP TYPE IF EXISTS notification_channel")

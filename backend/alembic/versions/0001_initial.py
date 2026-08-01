"""Initial schema: users, content_items, moderation_actions

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "moderator", "user", name="user_role"),
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "status",
            sa.Enum("active", "suspended", "deleted", name="user_status"),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "content_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "author_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "published", "removed", name="content_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )
    op.create_index("ix_content_items_author_id", "content_items", ["author_id"])
    op.create_index("ix_content_items_status", "content_items", ["status"])
    op.create_index("ix_content_items_created_at", "content_items", ["created_at"])

    op.create_table(
        "moderation_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "content_item_id",
            sa.String(36),
            sa.ForeignKey("content_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "moderator_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "verdict",
            sa.Enum("approved", "rejected", "escalated", name="moderation_verdict"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_moderation_actions_content_item_id", "moderation_actions", ["content_item_id"]
    )
    op.create_index(
        "ix_moderation_actions_moderator_id", "moderation_actions", ["moderator_id"]
    )
    op.create_index("ix_moderation_actions_verdict", "moderation_actions", ["verdict"])
    op.create_index("ix_moderation_actions_created_at", "moderation_actions", ["created_at"])


def downgrade() -> None:
    op.drop_table("moderation_actions")
    op.drop_table("content_items")
    op.drop_table("users")

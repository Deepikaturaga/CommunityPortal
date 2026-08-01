"""create content_items and processed_events tables

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_items",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("author_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "pending_review",
                "approved",
                "hidden",
                "deleted",
                name="contentstatus",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_content_items_entity_type", "content_items", ["entity_type"])
    op.create_index("ix_content_items_author_id", "content_items", ["author_id"])

    op.create_table(
        "processed_events",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_processed_event_key",
        "processed_events",
        ["entity_type", "entity_id", "version"],
    )


def downgrade() -> None:
    op.drop_table("processed_events")
    op.drop_index("ix_content_items_author_id", table_name="content_items")
    op.drop_index("ix_content_items_entity_type", table_name="content_items")
    op.drop_table("content_items")
    op.execute("DROP TYPE IF EXISTS contentstatus")

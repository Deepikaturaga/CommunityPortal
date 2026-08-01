"""Initial schema: users + media_assets tables.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── assetstatus enum ───────────────────────────────────────────────────────
    assetstatus = postgresql.ENUM(
        "pending", "confirmed", "deleted", name="assetstatus", create_type=False
    )
    assetstatus.create(op.get_bind(), checkfirst=True)

    # ── media_assets ───────────────────────────────────────────────────────────
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False, server_default="avatar"),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("declared_size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "confirmed", "deleted", name="assetstatus"),
            nullable=False,
            server_default="pending",
        ),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("s3_key"),
    )
    op.create_index("ix_media_assets_owner_id", "media_assets", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_media_assets_owner_id", table_name="media_assets")
    op.drop_table("media_assets")
    sa.Enum(name="assetstatus").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

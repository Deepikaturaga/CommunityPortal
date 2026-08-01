"""Initial schema: accounts and content_items tables.

Revision ID: 0001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_accounts_email", "accounts", ["email"])
    op.create_index("ix_accounts_username", "accounts", ["username"])

    content_status_enum = sa.Enum("draft", "published", "archived", name="contentstatus")
    content_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "content_items",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "status",
            content_status_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_items_owner_id", "content_items", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_content_items_owner_id", table_name="content_items")
    op.drop_table("content_items")
    op.drop_index("ix_accounts_username", table_name="accounts")
    op.drop_index("ix_accounts_email", table_name="accounts")
    op.drop_table("accounts")
    sa.Enum(name="contentstatus").drop(op.get_bind(), checkfirst=True)

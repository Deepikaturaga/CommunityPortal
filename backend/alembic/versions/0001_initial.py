"""Initial schema: users, content, moderation_audit_records.

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
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("user", "moderator", "admin", name="userrole"),
            nullable=False,
            server_default="user",
        ),
    )

    # --- content ---
    op.create_table(
        "content",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "author_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "active", "flagged", "locked", "hidden", "deleted",
                name="contentstatus",
            ),
            nullable=False,
            server_default="active",
            index=True,
        ),
        sa.Column("is_locked", sa.Boolean, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # --- moderation_audit_records (append-only) ---
    op.create_table(
        "moderation_audit_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "content_id",
            sa.String(36),
            sa.ForeignKey("content.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "moderator_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "action",
            sa.Enum("lock", "hide", "delete", name="moderationaction"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("previous_status", sa.String(32), nullable=False),
        sa.Column("new_status", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    # Note on DB-level immutability (AC-014.4):
    # In PostgreSQL production deployments, apply after migration:
    #   REVOKE UPDATE, DELETE ON moderation_audit_records FROM <app_role>;
    # SQLite does not support row-level privilege revocation; the ORM-level
    # event guards in app/models/moderation.py provide the enforcement layer.


def downgrade() -> None:
    op.drop_table("moderation_audit_records")
    op.drop_table("content")
    op.drop_table("users")
    # Drop enum types (PostgreSQL only; SQLite ignores)
    op.execute("DROP TYPE IF EXISTS moderationaction")
    op.execute("DROP TYPE IF EXISTS contentstatus")
    op.execute("DROP TYPE IF EXISTS userrole")

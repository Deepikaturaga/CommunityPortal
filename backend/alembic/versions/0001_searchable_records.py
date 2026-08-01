"""Alembic migration — initial: searchable_records table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_searchable_records"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "searchable_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("index_name", sa.String(255), nullable=False),
        sa.Column("document_type", sa.String(255), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_searchable_records_index_name", "searchable_records", ["index_name"])
    op.create_index(
        "ix_searchable_records_document_type", "searchable_records", ["document_type"]
    )
    op.create_index(
        "ix_searchable_records_content_hash", "searchable_records", ["content_hash"]
    )


def downgrade() -> None:
    op.drop_index("ix_searchable_records_content_hash")
    op.drop_index("ix_searchable_records_document_type")
    op.drop_index("ix_searchable_records_index_name")
    op.drop_table("searchable_records")

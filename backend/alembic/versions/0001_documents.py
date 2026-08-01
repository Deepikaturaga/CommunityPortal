"""Create documents table with visibility enum.

Revision ID: 0001_documents
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0001_documents"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    visibility_enum = sa.Enum(
        "public",
        "internal",
        "private",
        name="visibility_enum",
    )
    visibility_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "visibility",
            sa.Enum("public", "internal", "private", name="visibility_enum"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_title_trgm", "documents", ["title"], unique=False)
    op.create_index(
        op.f("ix_documents_visibility"), "documents", ["visibility"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_visibility"), table_name="documents")
    op.drop_index("ix_documents_title_trgm", table_name="documents")
    op.drop_table("documents")
    sa.Enum(name="visibility_enum").drop(op.get_bind(), checkfirst=True)

"""KB articles table — STORE-005 (TASK-030/TASK-044).

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE article_status_enum AS ENUM ('draft', 'published', 'archived')"
    )
    op.create_table(
        "kb_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(512), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "published",
                "archived",
                name="article_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
    op.create_index("ix_kb_articles_slug", "kb_articles", ["slug"], unique=True)
    op.create_index("ix_kb_articles_author_id", "kb_articles", ["author_id"])


def downgrade() -> None:
    op.drop_index("ix_kb_articles_author_id", table_name="kb_articles")
    op.drop_index("ix_kb_articles_slug", table_name="kb_articles")
    op.drop_table("kb_articles")
    op.execute("DROP TYPE article_status_enum")

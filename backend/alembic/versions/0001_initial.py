"""Initial schema — discussions and replies tables.

Revision ID: 0001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enums
    discussionstatus = sa.Enum("open", "locked", "hidden", name="discussionstatus")
    replystatus = sa.Enum("visible", "hidden", name="replystatus")
    discussionstatus.create(op.get_bind(), checkfirst=True)
    replystatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "discussions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "locked", "hidden", name="discussionstatus"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
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
    )
    op.create_index("ix_discussions_id", "discussions", ["id"])
    op.create_index("ix_discussions_author_id", "discussions", ["author_id"])

    op.create_table(
        "replies",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "discussion_id",
            sa.Integer(),
            sa.ForeignKey("discussions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("visible", "hidden", name="replystatus"),
            nullable=False,
            server_default="visible",
        ),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
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
    )
    op.create_index("ix_replies_id", "replies", ["id"])
    op.create_index("ix_replies_discussion_id", "replies", ["discussion_id"])
    op.create_index("ix_replies_author_id", "replies", ["author_id"])


def downgrade() -> None:
    op.drop_table("replies")
    op.drop_table("discussions")
    op.execute("DROP TYPE IF EXISTS replystatus")
    op.execute("DROP TYPE IF EXISTS discussionstatus")

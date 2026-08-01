"""create moderation_reports table

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "moderation_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reporter_id", sa.String(36), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column(
            "reason",
            sa.Enum(
                "spam",
                "harassment",
                "hate_speech",
                "misinformation",
                "violence",
                "other",
                name="report_reason_enum",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "reviewed",
                "dismissed",
                "actioned",
                name="report_status_enum",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_by", sa.String(36), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        # AC-015.2 — duplicate-report unique constraint
        sa.UniqueConstraint(
            "reporter_id",
            "target_id",
            name="uq_moderation_report_reporter_target",
        ),
    )
    op.create_index("ix_moderation_reports_reporter_id", "moderation_reports", ["reporter_id"])
    op.create_index("ix_moderation_reports_target_id", "moderation_reports", ["target_id"])
    op.create_index("ix_moderation_reports_status", "moderation_reports", ["status"])
    op.create_index("ix_moderation_reports_created_at", "moderation_reports", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_moderation_reports_created_at", "moderation_reports")
    op.drop_index("ix_moderation_reports_status", "moderation_reports")
    op.drop_index("ix_moderation_reports_target_id", "moderation_reports")
    op.drop_index("ix_moderation_reports_reporter_id", "moderation_reports")
    op.drop_table("moderation_reports")
    # SQLite does not support DROP TYPE; guard for Postgres
    try:
        op.execute("DROP TYPE IF EXISTS report_reason_enum")
        op.execute("DROP TYPE IF EXISTS report_status_enum")
    except Exception:
        pass

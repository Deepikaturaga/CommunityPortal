"""Add kb_revisions table with append-only DB trigger.

Revision ID : 0005_kb_revisions
Revises     : 0004_kb_articles   ← update if the real head differs
Create Date : 2025-01-01

AC-026.1  — table created as insert-only (trigger blocks UPDATE/DELETE at DB level)
IF-006    — revision history for KB articles
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# ── identifiers ──────────────────────────────────────────────────────────────
revision: str = "0005_kb_revisions"
down_revision: str = "0004_kb_articles"  # ← adjust to real current head
branch_labels = None
depends_on = None


# ── helpers ───────────────────────────────────────────────────────────────────

_TRIGGER_FUNC_SQL = """\
CREATE OR REPLACE FUNCTION kb_revisions_immutable()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'kb_revisions is append-only — % is forbidden (id=%)',
        TG_OP, OLD.id
        USING ERRCODE = 'raise_exception';
    RETURN NULL;
END;
$$;
"""

_TRIGGER_SQL = """\
CREATE TRIGGER trg_kb_revisions_immutable
BEFORE UPDATE OR DELETE ON kb_revisions
FOR EACH ROW EXECUTE FUNCTION kb_revisions_immutable();
"""

_DROP_TRIGGER_SQL = "DROP TRIGGER IF EXISTS trg_kb_revisions_immutable ON kb_revisions;"
_DROP_FUNC_SQL = "DROP FUNCTION IF EXISTS kb_revisions_immutable();"


# ── migration ─────────────────────────────────────────────────────────────────


def upgrade() -> None:
    op.create_table(
        "kb_revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("editor_id", sa.Integer(), nullable=True),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("title_snapshot", sa.Text(), nullable=False),
        sa.Column("content_snapshot", sa.Text(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["kb_articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["editor_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes
    op.create_index("ix_kb_revisions_article_id", "kb_revisions", ["article_id"])
    op.create_index("ix_kb_revisions_editor_id", "kb_revisions", ["editor_id"])
    op.create_index(
        "ix_kb_revisions_article_rev",
        "kb_revisions",
        ["article_id", "revision_number"],
        unique=True,
    )

    # Append-only trigger (PostgreSQL)
    op.execute(_TRIGGER_FUNC_SQL)
    op.execute(_TRIGGER_SQL)


def downgrade() -> None:
    op.execute(_DROP_TRIGGER_SQL)
    op.execute(_DROP_FUNC_SQL)
    op.drop_index("ix_kb_revisions_article_rev", table_name="kb_revisions")
    op.drop_index("ix_kb_revisions_editor_id", table_name="kb_revisions")
    op.drop_index("ix_kb_revisions_article_id", table_name="kb_revisions")
    op.drop_table("kb_revisions")

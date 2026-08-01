"""Initial taxonomy schema — categories, tags, association tables.

Revision ID: 0001_taxonomy
Revises: —
Create Date: 2025-01-01 00:00:00
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_taxonomy"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- TaxonomyStatus enum ---
    taxonomy_status = sa.Enum("active", "archived", name="taxonomystatus")
    taxonomy_status.create(op.get_bind(), checkfirst=True)

    # --- content stub table (FK target for association tables) ---
    op.create_table(
        "content",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(512), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_content"),
    )

    # --- categories ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("label", sa.String(256), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="taxonomystatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            name="fk_categories_parent_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    # --- tags ---
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("label", sa.String(256), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="taxonomystatus"),
            nullable=False,
            server_default="active",
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
        sa.PrimaryKeyConstraint("id", name="pk_tags"),
        sa.UniqueConstraint("slug", name="uq_tags_slug"),
    )
    op.create_index("ix_tags_slug", "tags", ["slug"], unique=True)

    # --- content_category association ---
    op.create_table(
        "content_category",
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_content_category_category_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["content.id"],
            name="fk_content_category_content_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("content_id", "category_id", name="uq_content_category"),
    )

    # --- content_tag association ---
    op.create_table(
        "content_tag",
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
            name="fk_content_tag_tag_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["content.id"],
            name="fk_content_tag_content_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("content_id", "tag_id", name="uq_content_tag"),
    )


def downgrade() -> None:
    op.drop_table("content_tag")
    op.drop_table("content_category")
    op.drop_index("ix_tags_slug", "tags")
    op.drop_table("tags")
    op.drop_index("ix_categories_parent_id", "categories")
    op.drop_index("ix_categories_slug", "categories")
    op.drop_table("categories")
    op.drop_table("content")
    sa.Enum(name="taxonomystatus").drop(op.get_bind(), checkfirst=True)

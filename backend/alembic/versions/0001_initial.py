"""Initial schema: users, login_attempts, mfa_challenges.

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enums -----------------------------------------------------------
    accountstatus = sa.Enum(
        "unverified", "active", "locked", "suspended", "deactivated",
        name="accountstatus",
    )
    mfamethod = sa.Enum(
        "none", "totp", "email_otp",
        name="mfamethod",
    )
    accountstatus.create(op.get_bind(), checkfirst=True)
    mfamethod.create(op.get_bind(), checkfirst=True)

    # --- users -----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "unverified", "active", "locked", "suspended", "deactivated",
                name="accountstatus",
            ),
            nullable=False,
            server_default="unverified",
        ),
        sa.Column(
            "mfa_method",
            sa.Enum("none", "totp", "email_otp", name="mfamethod"),
            nullable=False,
            server_default="none",
        ),
        sa.Column("totp_secret", sa.Text, nullable=True),
        sa.Column("mfa_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("failed_login_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_status", "users", ["status"])

    # --- login_attempts --------------------------------------------------
    op.create_table(
        "login_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("detail", sa.String(255), nullable=True),
    )
    op.create_index(
        "ix_login_attempts_user_id_occurred_at",
        "login_attempts",
        ["user_id", "occurred_at"],
    )

    # --- mfa_challenges --------------------------------------------------
    op.create_table(
        "mfa_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("challenge_token", sa.String(512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_mfa_challenges_challenge_token", "mfa_challenges", ["challenge_token"], unique=True
    )
    op.create_index("ix_mfa_challenges_user_id", "mfa_challenges", ["user_id"])


def downgrade() -> None:
    op.drop_table("mfa_challenges")
    op.drop_table("login_attempts")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_table("users")
    sa.Enum(name="mfamethod").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="accountstatus").drop(op.get_bind(), checkfirst=True)

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Account aggregates
# ---------------------------------------------------------------------------


class AccountStats(BaseModel):
    """Total and breakdown of registered accounts."""

    total: int = Field(ge=0, description="Total user accounts")
    active: int = Field(ge=0, description="Accounts with status=active")
    suspended: int = Field(ge=0, description="Accounts with status=suspended")
    deleted: int = Field(ge=0, description="Accounts with status=deleted")
    admins: int = Field(ge=0, description="Accounts with role=admin")
    moderators: int = Field(ge=0, description="Accounts with role=moderator")
    regular_users: int = Field(ge=0, description="Accounts with role=user")
    new_last_30_days: int = Field(ge=0, description="Accounts registered in last 30 days")


# ---------------------------------------------------------------------------
# Content volume aggregates
# ---------------------------------------------------------------------------


class ContentVolumeStats(BaseModel):
    """Total and status breakdown of content items."""

    total: int = Field(ge=0, description="Total content items")
    pending: int = Field(ge=0, description="Items awaiting moderation")
    published: int = Field(ge=0, description="Items with status=published")
    removed: int = Field(ge=0, description="Items with status=removed")
    new_last_30_days: int = Field(ge=0, description="Items created in last 30 days")


# ---------------------------------------------------------------------------
# Moderation aggregates
# ---------------------------------------------------------------------------


class ModerationStats(BaseModel):
    """Totals and verdict breakdown for moderation actions."""

    total_actions: int = Field(ge=0, description="Total moderation actions recorded")
    approved: int = Field(ge=0, description="Actions with verdict=approved")
    rejected: int = Field(ge=0, description="Actions with verdict=rejected")
    escalated: int = Field(ge=0, description="Actions with verdict=escalated")
    actions_last_30_days: int = Field(
        ge=0, description="Moderation actions in last 30 days"
    )
    pending_items: int = Field(
        ge=0, description="Content items still awaiting any moderation action"
    )


# ---------------------------------------------------------------------------
# Top-level dashboard response
# ---------------------------------------------------------------------------


class DashboardResponse(BaseModel):
    """Aggregated admin dashboard figures (IF-011 / COMP-009)."""

    generated_at: datetime = Field(description="UTC timestamp when this snapshot was computed")
    accounts: AccountStats
    content: ContentVolumeStats
    moderation: ModerationStats

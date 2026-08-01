"""Pydantic schemas for the member profile resource (IF-003 / COMP-002)."""
import uuid
from datetime import datetime
from typing import Annotated

from markupsafe import escape
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _html_escape(value: str | None) -> str | None:
    """Context-appropriate output encoding for free-text fields (VER-010)."""
    if value is None:
        return None
    return str(escape(value))


class ProfileResponse(BaseModel):
    """Read-only representation of a member's own profile (AC-007.x)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: Annotated[str | None, Field(default=None)]
    bio: Annotated[str | None, Field(default=None)]
    location: Annotated[str | None, Field(default=None)]
    website_url: Annotated[str | None, Field(default=None)]
    created_at: datetime
    updated_at: datetime

    @field_validator("display_name", "bio", "location", mode="after")
    @classmethod
    def encode_free_text(cls, v: str | None) -> str | None:
        """HTML-escape free-text fields before returning to callers (VER-010)."""
        return _html_escape(v)


class ProfileUpdateRequest(BaseModel):
    """Partial update payload for PUT /api/v1/profile."""

    display_name: Annotated[
        str | None,
        Field(default=None, max_length=100, description="Visible name (≤100 chars)"),
    ]
    bio: Annotated[
        str | None,
        Field(default=None, max_length=2000, description="Free-text biography (≤2000 chars)"),
    ]
    location: Annotated[
        str | None,
        Field(default=None, max_length=100, description="Location string (≤100 chars)"),
    ]
    website_url: Annotated[
        str | None,
        Field(default=None, max_length=2048, description="Personal website URL (≤2048 chars)"),
    ]

    @field_validator("website_url", mode="after")
    @classmethod
    def validate_website_url(cls, v: str | None) -> str | None:
        """Reject URLs with non-http(s) schemes to prevent javascript: injection."""
        if v is None:
            return v
        lower = v.strip().lower()
        if lower and not (lower.startswith("https://") or lower.startswith("http://")):

            raise ValueError("website_url must start with http:// or https://")
        return v

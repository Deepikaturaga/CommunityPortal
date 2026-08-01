"""Pydantic request/response schemas for the search API (IF-014)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.services.search.models import Visibility

# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

_MAX_QUERY_LEN = 200
_MAX_LIMIT = 100


class SearchRequest(BaseModel):
    """Validated query parameters for GET /api/v1/search."""

    q: Annotated[
        str,
        Field(
            min_length=1,
            max_length=_MAX_QUERY_LEN,
            description="Free-text search term (matched against title and body).",
        ),
    ]
    limit: Annotated[
        int,
        Field(default=20, ge=1, le=_MAX_LIMIT, description="Maximum results to return."),
    ] = 20
    offset: Annotated[
        int,
        Field(default=0, ge=0, description="Pagination offset."),
    ] = 0

    @field_validator("q")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query must not be blank after stripping whitespace.")
        return v


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class DocumentResult(BaseModel):
    """Single document hit returned by the search API."""

    model_config = {"from_attributes": True}

    id: int
    title: str
    visibility: Visibility
    created_at: datetime


class SearchResponse(BaseModel):
    """Envelope for GET /api/v1/search results (AC-027.3 empty-state)."""

    total: int = Field(description="Total matching documents (before pagination).")
    items: list[DocumentResult] = Field(description="Page of results; empty list when none found.")
    query: str = Field(description="Echo of the normalised search term.")
    limit: int
    offset: int

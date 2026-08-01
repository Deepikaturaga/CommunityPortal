"""Post-service Pydantic schemas.

Covers AC-016 (create), AC-017 (read), AC-018 (list/pagination),
AC-019 (update), AC-020 (delete / soft-delete), AC-021 (rate limiting).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models.content import ContentStatus

# ---------------------------------------------------------------------------
# Shared field types
# ---------------------------------------------------------------------------
TitleStr = Annotated[str, StringConstraints(min_length=1, max_length=512, strip_whitespace=True)]
BodyStr = Annotated[str, StringConstraints(min_length=1, max_length=65_535, strip_whitespace=True)]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------
class PostCreateRequest(BaseModel):
    """AC-016.1 — required fields for post creation."""

    title: TitleStr
    body: BodyStr


class PostUpdateRequest(BaseModel):
    """AC-019.1 — all fields are optional (PATCH semantics)."""

    title: TitleStr | None = None
    body: BodyStr | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class PostOut(BaseModel):
    """AC-017.1 — single-post response shape."""

    model_config = {"from_attributes": True}

    id: str
    author_id: str
    title: str
    body: str
    status: ContentStatus
    is_locked: bool
    created_at: datetime
    updated_at: datetime


class PostPage(BaseModel):
    """AC-018.1 — paginated list response."""

    items: list[PostOut]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Validation-error shape (contract)
# ---------------------------------------------------------------------------
class FieldError(BaseModel):
    loc: list[str]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    detail: list[FieldError]

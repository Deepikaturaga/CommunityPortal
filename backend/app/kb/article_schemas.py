"""KB article request / response schemas (IF-007)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.kb.article_models import ArticleStatus


class ArticleCreate(BaseModel):
    """Request body for POST /api/v1/kb/articles (IF-007)."""

    title: str = Field(min_length=1, max_length=512)
    body: str = Field(
        min_length=1,
        description="HTML body — will be sanitized server-side before storage (AC-022.3).",
    )
    status: ArticleStatus = ArticleStatus.DRAFT

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()


class ArticleRead(BaseModel):
    """Response schema for a KB article."""

    id: uuid.UUID
    title: str
    body: str
    slug: str
    status: ArticleStatus
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

"""Taxonomy Pydantic schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class VocabularyCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)
    name: str = Field(max_length=255)
    description: str | None = None


class VocabularyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class VocabularyRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    slug: str
    name: str
    description: str | None = None


class TermCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)
    name: str = Field(max_length=255)
    description: str | None = None


class TermUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class TermRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    vocabulary_id: str
    slug: str
    name: str
    description: str | None = None
    created_by: str | None = None

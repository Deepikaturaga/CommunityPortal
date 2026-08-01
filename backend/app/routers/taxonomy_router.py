"""Taxonomy router – /api/v1/taxonomy endpoints.

Authorization matrix:
  GET    /taxonomy/vocabularies          → all authenticated roles
  POST   /taxonomy/vocabularies          → EDITOR, ADMIN, SUPERADMIN
  PATCH  /taxonomy/vocabularies/{id}     → EDITOR, ADMIN, SUPERADMIN
  DELETE /taxonomy/vocabularies/{id}     → ADMIN, SUPERADMIN

  GET    /taxonomy/vocabularies/{id}/terms       → all authenticated roles
  POST   /taxonomy/vocabularies/{id}/terms       → CONTRIBUTOR, EDITOR, ADMIN, SUPERADMIN
  PATCH  /taxonomy/vocabularies/{id}/terms/{tid} → EDITOR, ADMIN, SUPERADMIN
  DELETE /taxonomy/vocabularies/{id}/terms/{tid} → ADMIN, SUPERADMIN
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_min_role, require_role
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.taxonomy import TaxonomyTerm, TaxonomyVocabulary
from app.models.user import User
from app.schemas.taxonomy_schemas import (
    TermCreate,
    TermRead,
    TermUpdate,
    VocabularyCreate,
    VocabularyRead,
    VocabularyUpdate,
)

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])

# ──────────────────────────────────────────────────────────────────────────────
# Vocabulary endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/vocabularies", response_model=list[VocabularyRead], summary="List vocabularies")
async def list_vocabularies(
    _caller: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VocabularyRead]:
    result = await db.execute(select(TaxonomyVocabulary))
    return [VocabularyRead.model_validate(v) for v in result.scalars().all()]


@router.post(
    "/vocabularies",
    response_model=VocabularyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create vocabulary (editor+)",
)
async def create_vocabulary(
    body: VocabularyCreate,
    _caller: User = Depends(require_min_role(UserRole.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> VocabularyRead:
    result = await db.execute(
        select(TaxonomyVocabulary).where(TaxonomyVocabulary.slug == body.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
    vocab = TaxonomyVocabulary(slug=body.slug, name=body.name, description=body.description)
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    return VocabularyRead.model_validate(vocab)


@router.patch(
    "/vocabularies/{vocab_id}",
    response_model=VocabularyRead,
    summary="Update vocabulary (editor+)",
)
async def update_vocabulary(
    vocab_id: str,
    body: VocabularyUpdate,
    _caller: User = Depends(require_min_role(UserRole.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> VocabularyRead:
    result = await db.execute(
        select(TaxonomyVocabulary).where(TaxonomyVocabulary.id == vocab_id)
    )
    vocab = result.scalar_one_or_none()
    if vocab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary not found")
    if body.name is not None:
        vocab.name = body.name
    if body.description is not None:
        vocab.description = body.description
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    return VocabularyRead.model_validate(vocab)


@router.delete(
    "/vocabularies/{vocab_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete vocabulary (admin+)",
)
async def delete_vocabulary(
    vocab_id: str,
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(TaxonomyVocabulary).where(TaxonomyVocabulary.id == vocab_id)
    )
    vocab = result.scalar_one_or_none()
    if vocab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary not found")
    await db.delete(vocab)
    await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Term endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/vocabularies/{vocab_id}/terms",
    response_model=list[TermRead],
    summary="List terms",
)
async def list_terms(
    vocab_id: str,
    _caller: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TermRead]:
    result = await db.execute(
        select(TaxonomyTerm).where(TaxonomyTerm.vocabulary_id == vocab_id)
    )
    return [TermRead.model_validate(t) for t in result.scalars().all()]


@router.post(
    "/vocabularies/{vocab_id}/terms",
    response_model=TermRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create term (contributor+)",
)
async def create_term(
    vocab_id: str,
    body: TermCreate,
    caller: User = Depends(require_min_role(UserRole.CONTRIBUTOR)),
    db: AsyncSession = Depends(get_db),
) -> TermRead:
    result = await db.execute(
        select(TaxonomyVocabulary).where(TaxonomyVocabulary.id == vocab_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary not found")
    term = TaxonomyTerm(
        vocabulary_id=vocab_id,
        slug=body.slug,
        name=body.name,
        description=body.description,
        created_by=caller.id,
    )
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return TermRead.model_validate(term)


@router.patch(
    "/vocabularies/{vocab_id}/terms/{term_id}",
    response_model=TermRead,
    summary="Update term (editor+)",
)
async def update_term(
    vocab_id: str,
    term_id: str,
    body: TermUpdate,
    _caller: User = Depends(require_min_role(UserRole.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> TermRead:
    result = await db.execute(
        select(TaxonomyTerm).where(
            TaxonomyTerm.id == term_id, TaxonomyTerm.vocabulary_id == vocab_id
        )
    )
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    if body.name is not None:
        term.name = body.name
    if body.description is not None:
        term.description = body.description
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return TermRead.model_validate(term)


@router.delete(
    "/vocabularies/{vocab_id}/terms/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete term (admin+)",
)
async def delete_term(
    vocab_id: str,
    term_id: str,
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(TaxonomyTerm).where(
            TaxonomyTerm.id == term_id, TaxonomyTerm.vocabulary_id == vocab_id
        )
    )
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    await db.delete(term)
    await db.commit()

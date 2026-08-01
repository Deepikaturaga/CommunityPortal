"""FastAPI router for GET /api/v1/search (IF-014)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.core.security import TokenData, get_current_user
from app.services.search.query import search_documents
from app.services.search.schemas import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search documents (IF-014)",
    description=(
        "Full-text search over indexed documents. "
        "Results are filtered by the caller's role: "
        "`admin` sees all, `editor` sees public+internal, `viewer` sees public only."
    ),
)
async def search(
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    q: Annotated[
        str,
        Query(min_length=1, max_length=200, description="Search term"),
    ],
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
) -> SearchResponse:
    req = SearchRequest(q=q, limit=limit, offset=offset)
    return await search_documents(req, role=current_user.role, db=db)

"""Search service — parameterized query with role-aware visibility filter (IF-014).

Security: every query uses SQLAlchemy bound parameters; no string interpolation into
SQL (AC-027.4 / OWASP A03 Injection).
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search.models import Document, Visibility
from app.services.search.schemas import DocumentResult, SearchRequest, SearchResponse

# ---------------------------------------------------------------------------
# Role → permitted visibility levels
# ---------------------------------------------------------------------------

_VISIBILITY_BY_ROLE: dict[str, list[Visibility]] = {
    "admin": [Visibility.public, Visibility.internal, Visibility.private],
    "editor": [Visibility.public, Visibility.internal],
    "viewer": [Visibility.public],
}
"""Explicit allow-list: deny by default for unknown roles."""


def _allowed_visibilities(role: str) -> list[Visibility]:
    """Return the visibility levels the given role may see.

    Unknown roles are treated as the most-restrictive tier (viewer/public only).
    """
    return _VISIBILITY_BY_ROLE.get(role, [Visibility.public])


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


async def search_documents(
    request: SearchRequest,
    role: str,
    db: AsyncSession,
) -> SearchResponse:
    """Execute a safe, parameterized full-text search with visibility filtering.

    AC-027.4: the search term is passed as a bound parameter to ILIKE — never
              interpolated into the query string.
    AC-027.3: returns an empty ``items`` list (total=0) when nothing matches.
    """
    allowed = _allowed_visibilities(role)

    # Parameterized ILIKE pattern — SQLAlchemy binds the value, never interpolates.
    # The `%` wildcards are part of the *Python* value, not raw SQL.
    pattern = f"%{request.q}%"

    base_stmt = (
        select(Document)
        .where(
            Document.visibility.in_(allowed),  # role-aware filter
            or_(
                Document.title.ilike(pattern),   # bound param
                Document.body.ilike(pattern),    # bound param
            ),
        )
        .order_by(Document.created_at.desc())
    )

    # Total count (separate query so pagination is accurate)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    # Paginated page
    page_stmt = base_stmt.offset(request.offset).limit(request.limit)
    rows = (await db.execute(page_stmt)).scalars().all()

    items = [DocumentResult.model_validate(row) for row in rows]

    return SearchResponse(
        total=total,
        items=items,
        query=request.q,
        limit=request.limit,
        offset=request.offset,
    )

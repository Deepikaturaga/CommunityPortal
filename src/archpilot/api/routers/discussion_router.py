"""Discussion threads router — IF-004 / COMP-003.

Endpoints
---------
POST   /api/discussion/sessions/{session_id}/threads        — AC-009.1
GET    /api/discussion/sessions/{session_id}/threads        — AC-011.1-5
GET    /api/discussion/sessions/{session_id}/threads/{id}   — single fetch
PATCH  /api/discussion/sessions/{session_id}/threads/{id}   — partial update
DELETE /api/discussion/sessions/{session_id}/threads/{id}   — hard delete

Authentication
--------------
All endpoints require a valid Cognito JWT (get_current_user).
Mutation endpoints additionally enforce resource ownership at the service
layer (OWASP A01 — Broken Access Control).

Note on FastAPI 0.115 + PEP 563 (from __future__ import annotations)
----------------------------------------------------------------------
With PEP 563 all annotations become strings at module load time.  FastAPI's
``is_body_allowed_for_status_code`` guard on 204 routes cannot resolve the
string ``"None"`` back to ``NoneType``, so the DELETE endpoint must carry an
explicit ``response_model=None`` to suppress the response-body check.
"""
from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status as http_status

from archpilot.api.cognito_auth import CognitoUser, get_current_user
from archpilot.services.discussion.threads import (
    CreateThreadRequest,
    DuplicateTitleError,
    SortDirection,
    SortField,
    ThreadListResponse,
    ThreadNotFoundError,
    ThreadOwnershipError,
    ThreadResponse,
    ThreadService,
    ThreadStatus,
    UpdateThreadRequest,
    get_thread_service,
)

logger = logging.getLogger(__name__)

discussion_router = APIRouter(prefix="/discussion", tags=["discussion"])

_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100

SessionIdPath = Annotated[
    str,
    Path(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Owning session identifier.",
    ),
]

ThreadIdPath = Annotated[
    str,
    Path(
        ...,
        min_length=36,
        max_length=36,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        description="Thread UUID.",
    ),
]


def _handle_service_error(exc: Exception, operation: str) -> None:
    """Map service-layer exceptions to HTTP status codes (OWASP A09 — no internals leaked)."""
    if isinstance(exc, ThreadNotFoundError):
        raise HTTPException(status_code=404, detail=f"Thread not found: {exc}")
    if isinstance(exc, DuplicateTitleError):
        raise HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ThreadOwnershipError):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to modify this thread.",
        )
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc))
    logger.exception("[discussion] Unexpected error during %s", operation)
    raise HTTPException(status_code=500, detail="An unexpected error occurred.")


# ---------------------------------------------------------------------------
# POST — create thread (AC-009.1)
# ---------------------------------------------------------------------------

@discussion_router.post(
    "/sessions/{session_id}/threads",
    response_model=ThreadResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create a discussion thread (AC-009.1)",
    responses={
        409: {"description": "Duplicate thread title in this session (AC-009.2)"},
        422: {"description": "Validation error — title or body failed sanitization"},
    },
)
async def create_thread(
    session_id: SessionIdPath,
    request: CreateThreadRequest,
    user: CognitoUser = Depends(get_current_user),
    svc: ThreadService = Depends(get_thread_service),
) -> ThreadResponse:
    """Create a discussion thread.

    Title/body are HTML-stripped (AC-009.3), user_sub stamped (AC-009.4).
    """
    logger.info(
        "[discussion] create thread session=%s user=%s title=%r",
        session_id,
        user.sub,
        request.title,
    )
    try:
        return svc.create_thread(session_id=session_id, user_sub=user.sub, request=request)
    except (DuplicateTitleError, ThreadOwnershipError, ThreadNotFoundError, ValueError) as exc:
        _handle_service_error(exc, "create_thread")


# ---------------------------------------------------------------------------
# GET — list threads (AC-011.x)
# ---------------------------------------------------------------------------

@discussion_router.get(
    "/sessions/{session_id}/threads",
    response_model=ThreadListResponse,
    status_code=http_status.HTTP_200_OK,
    summary="List discussion threads with filter/sort/paginate (AC-011.x)",
)
async def list_threads(
    session_id: SessionIdPath,
    status_filter: Optional[ThreadStatus] = Query(
        None, alias="status", description="Filter by status (AC-011.2)."
    ),
    sort_by: SortField = Query(SortField.created_at, description="Sort field (AC-011.3)."),
    direction: SortDirection = Query(
        SortDirection.desc, description="Sort direction (AC-011.3)."
    ),
    keyword: Optional[str] = Query(
        None, max_length=256, description="Keyword search in title/body (AC-011.4)."
    ),
    limit: int = Query(
        _DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE, description="Page size 1-100 (AC-011.5)."
    ),
    cursor: Optional[str] = Query(None, description="Pagination cursor (AC-011.5)."),
    user: CognitoUser = Depends(get_current_user),
    svc: ThreadService = Depends(get_thread_service),
) -> ThreadListResponse:
    """Paginated, filtered, sorted thread list. Pass next_cursor for subsequent pages."""
    logger.info(
        "[discussion] list threads session=%s user=%s status=%s sort=%s dir=%s kw=%r limit=%d",
        session_id,
        user.sub,
        status_filter,
        sort_by,
        direction,
        keyword,
        limit,
    )
    try:
        return svc.list_threads(
            session_id=session_id,
            status=status_filter,
            sort_by=sort_by,
            direction=direction,
            keyword=keyword,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        _handle_service_error(exc, "list_threads")


# ---------------------------------------------------------------------------
# GET — single thread
# ---------------------------------------------------------------------------

@discussion_router.get(
    "/sessions/{session_id}/threads/{thread_id}",
    response_model=ThreadResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Fetch a single discussion thread",
    responses={404: {"description": "Thread not found"}},
)
async def get_thread(
    session_id: SessionIdPath,
    thread_id: ThreadIdPath,
    user: CognitoUser = Depends(get_current_user),
    svc: ThreadService = Depends(get_thread_service),
) -> ThreadResponse:
    try:
        return svc.get_thread(session_id=session_id, thread_id=thread_id)
    except (ThreadNotFoundError, ValueError) as exc:
        _handle_service_error(exc, "get_thread")


# ---------------------------------------------------------------------------
# PATCH — update thread
# ---------------------------------------------------------------------------

@discussion_router.patch(
    "/sessions/{session_id}/threads/{thread_id}",
    response_model=ThreadResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Partially update a discussion thread",
    responses={
        403: {"description": "Not the thread owner"},
        404: {"description": "Thread not found"},
        409: {"description": "Duplicate title"},
    },
)
async def update_thread(
    session_id: SessionIdPath,
    thread_id: ThreadIdPath,
    request: UpdateThreadRequest,
    user: CognitoUser = Depends(get_current_user),
    svc: ThreadService = Depends(get_thread_service),
) -> ThreadResponse:
    try:
        return svc.update_thread(
            session_id=session_id,
            thread_id=thread_id,
            user_sub=user.sub,
            request=request,
        )
    except (ThreadNotFoundError, ThreadOwnershipError, DuplicateTitleError, ValueError) as exc:
        _handle_service_error(exc, "update_thread")


# ---------------------------------------------------------------------------
# DELETE — hard delete
#
# ``response_model=None`` is required when ``from __future__ import annotations``
# is active.  PEP 563 turns the ``-> None`` return annotation into the string
# literal "None", which FastAPI 0.115 cannot resolve before its
# ``is_body_allowed_for_status_code(204)`` assertion fires.  Supplying
# ``response_model=None`` explicitly bypasses the annotation-inspection path.
# ---------------------------------------------------------------------------

@discussion_router.delete(
    "/sessions/{session_id}/threads/{thread_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_thread(
    session_id: SessionIdPath,
    thread_id: ThreadIdPath,
    user: CognitoUser = Depends(get_current_user),
    svc: ThreadService = Depends(get_thread_service),
) -> None:
    """Hard-delete a thread. Returns 204 on success, 403 if not owner, 404 if not found."""
    try:
        svc.delete_thread(session_id=session_id, thread_id=thread_id, user_sub=user.sub)
    except (ThreadNotFoundError, ThreadOwnershipError, ValueError) as exc:
        _handle_service_error(exc, "delete_thread")

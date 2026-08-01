from __future__ import annotations

"""Global exception handlers registered on the canonical FastAPI app."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.discussion.exceptions import (
    DiscussionHiddenError,
    DiscussionLockedError,
    DiscussionNotFoundError,
    ReplyBodyTooLongError,
    ReplyBodyTooShortError,
    ReplyForbiddenError,
    ReplyHiddenError,
    ReplyNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DiscussionNotFoundError)
    async def discussion_not_found(
        _request: Request, exc: DiscussionNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Discussion not found."})

    @app.exception_handler(DiscussionLockedError)
    async def discussion_locked(
        _request: Request, exc: DiscussionLockedError
    ) -> JSONResponse:
        # AC-010.2: locked thread → 423 Locked
        return JSONResponse(
            status_code=423,
            content={"detail": "This discussion is locked and no longer accepts replies."},
        )

    @app.exception_handler(DiscussionHiddenError)
    async def discussion_hidden(
        _request: Request, exc: DiscussionHiddenError
    ) -> JSONResponse:
        # Opaque 404 — never reveal hidden status to non-moderators (AC-012.3)
        return JSONResponse(status_code=404, content={"detail": "Discussion not found."})

    @app.exception_handler(ReplyNotFoundError)
    async def reply_not_found(_request: Request, exc: ReplyNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Reply not found."})

    @app.exception_handler(ReplyForbiddenError)
    async def reply_forbidden(_request: Request, exc: ReplyForbiddenError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"detail": "You are not authorised to modify this reply."},
        )

    @app.exception_handler(ReplyHiddenError)
    async def reply_hidden(_request: Request, exc: ReplyHiddenError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Reply not found."})

    @app.exception_handler(ReplyBodyTooShortError)
    async def reply_too_short(
        _request: Request, exc: ReplyBodyTooShortError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ReplyBodyTooLongError)
    async def reply_too_long(_request: Request, exc: ReplyBodyTooLongError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

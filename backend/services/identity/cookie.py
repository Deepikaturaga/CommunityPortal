"""
Cookie-issuance helpers for session management.

Centralises all HttpOnly / Secure / SameSite cookie logic so every
endpoint that needs to set or clear a session cookie calls one function
and the security defaults are never accidentally bypassed.

OWASP A07 / cookie security
-----------------------------
* HttpOnly  — prevents JS access (mitigates XSS token theft).
* Secure    — cookie only sent over HTTPS.
* SameSite  — lax by default; strict for higher-assurance flows.
* Domain / Path scoped to application settings.
* Max-Age   — mirrors the server-side session TTL exactly so the browser
              does not retain a stale cookie after the server-side record
              has expired.
"""

from __future__ import annotations

from fastapi import Response

from backend.app.core.config import Settings


def set_session_cookie(
    response: Response,
    session_id: str,
    settings: Settings,
    *,
    max_age: int | None = None,
) -> None:
    """
    Write the session cookie onto *response*.

    Parameters
    ----------
    response:
        The FastAPI / Starlette ``Response`` object to mutate.
    session_id:
        Signed, opaque session ID returned by :class:`SessionStore.create`.
    settings:
        Application settings (controls all cookie attributes).
    max_age:
        Override TTL in seconds; defaults to ``settings.session_cookie_max_age``.
    """
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        max_age=max_age if max_age is not None else settings.session_cookie_max_age,
        path=settings.session_cookie_path,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=settings.session_cookie_httponly,
        samesite=settings.session_cookie_samesite,
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    """
    Expire the session cookie on *response* (set Max-Age=0).

    Called during logout / session invalidation so the browser immediately
    discards the cookie even if the user ignores the redirect.
    """
    response.delete_cookie(
        key=settings.session_cookie_name,
        path=settings.session_cookie_path,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=settings.session_cookie_httponly,
        samesite=settings.session_cookie_samesite,
    )

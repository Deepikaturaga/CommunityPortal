"""
FastAPI dependency injectors for the identity session store.

Import and use these in route handlers instead of constructing
``SessionStore`` directly.

Example
-------
::

    @router.post("/login")
    async def login(
        response: Response,
        store: SessionStoreDep,
        settings: SettingsDep,
    ) -> ...:
        session_id, _ = await store.create({"user_id": user.id})
        set_session_cookie(response, session_id, settings)
        return {"ok": True}


    @router.get("/me")
    async def me(
        session: CurrentSessionDep,
    ) -> ...:
        return session
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status

from backend.app.core.config import Settings, get_settings
from backend.services.identity.session_store import (
    SessionNotFoundError,
    SessionSignatureError,
    SessionStore,
    SessionStoreError,
)


# ---------------------------------------------------------------------------
# Settings dependency
# ---------------------------------------------------------------------------


def get_settings_dep() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


# ---------------------------------------------------------------------------
# Redis pool → SessionStore dependency
# ---------------------------------------------------------------------------


def get_session_store(request: Request, settings: SettingsDep) -> SessionStore:
    """
    Resolve the shared ``SessionStore`` from application lifespan state.

    The ``ConnectionPool`` must be placed on ``app.state.redis_pool`` during
    startup (see ``backend/app/main.py`` lifespan).
    """
    pool = getattr(request.app.state, "redis_pool", None)
    if pool is None:
        raise RuntimeError(
            "Redis connection pool not initialised. "
            "Ensure create_redis_pool() is called in the app lifespan."
        )
    return SessionStore(pool=pool, settings=settings)


SessionStoreDep = Annotated[SessionStore, Depends(get_session_store)]


# ---------------------------------------------------------------------------
# Current-session dependency (reads + validates the inbound cookie)
# ---------------------------------------------------------------------------


async def get_current_session_from_request(
    request: Request,
    store: SessionStoreDep,
    settings: SettingsDep,
) -> dict[str, Any]:
    """
    Request-aware variant that reads the cookie name from settings so it
    honours ``session_cookie_name`` regardless of its configured value.

    * Reads the session cookie (named from settings).
    * Verifies the HMAC signature.
    * Looks up the data in Redis, refreshing the sliding-window TTL.
    * Raises ``401 Unauthorized`` on any error so callers never receive
      partial or unauthenticated session state.

    Use :data:`CurrentSessionDep` in route signatures.
    """
    raw = request.cookies.get(settings.session_cookie_name)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )
    try:
        data = await store.read(raw)
    except SessionSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session.",
        ) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or not found.",
        ) from exc
    except SessionStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session store unavailable.",
        ) from exc
    return data


CurrentSessionDep = Annotated[dict[str, Any], Depends(get_current_session_from_request)]

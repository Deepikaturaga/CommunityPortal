"""
Session-store client backed by ElastiCache (Redis-compatible).

Design decisions
----------------
* Session IDs are 32-byte cryptographically random values, URL-safe base-64
  encoded (43 chars), then HMAC-SHA256-signed and stored as
  ``<token>.<signature>`` so forged / tampered IDs are rejected before a
  Redis round-trip.
* All session data is serialised to JSON (never pickle) to prevent remote
  code-execution on deserialization.
* Redis keys are namespaced: ``session:<token>`` where ``token`` is the raw
  (unsigned) portion.  The signature is never persisted; it is only verified
  on the client-supplied value.
* TTL is refreshed ("sliding window") on every successful read so active
  sessions stay alive.
* The ``expire`` method hard-expires a session immediately (UNLINK).
* The ``invalidate`` method is an alias kept for semantic clarity
  (logout vs. hard expiry by admin/policy).
* All network operations are async (redis.asyncio); blocking code must not
  call these methods from the event loop.
* Connection pool is created once at application startup (lifespan) and
  injected via FastAPI dependency — never created per-request.

OWASP controls applied
-----------------------
A02 – session data is encrypted-in-transit via ``rediss://`` URLs on AWS;
      signing prevents ID oracle attacks.
A07 – IDs are generated with ``secrets.token_bytes``; no sequential / guessable IDs.
A04 – TTL enforced server-side; clients cannot extend sessions.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool
from redis.exceptions import RedisError

from backend.app.core.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SessionStoreError(Exception):
    """Raised when the session store encounters an unrecoverable error."""


class SessionNotFoundError(SessionStoreError):
    """Raised when no session exists for the supplied session ID."""


class SessionSignatureError(SessionStoreError):
    """Raised when an incoming session ID has an invalid / forged signature."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ID_BYTES = 32  # 256-bit random token
_SEP = "."


def _generate_token() -> str:
    """Return a cryptographically random, URL-safe base-64 token (no padding)."""
    return secrets.token_urlsafe(_ID_BYTES)


def _sign(token: str, secret: str) -> str:
    """Return HMAC-SHA256 hex digest of *token* using *secret*."""
    return hmac.new(
        secret.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()


def _make_session_id(token: str, secret: str) -> str:
    """Combine token + signature into the opaque session ID given to the client."""
    sig = _sign(token, secret)
    return f"{token}{_SEP}{sig}"


def _verify_session_id(session_id: str, secret: str) -> str:
    """
    Verify the session-ID signature and return the raw token.

    Raises
    ------
    SessionSignatureError
        If the session ID is malformed or the signature does not match.
    """
    parts = session_id.split(_SEP, maxsplit=1)
    if len(parts) != 2:  # noqa: PLR2004
        raise SessionSignatureError("Malformed session ID: missing signature segment.")
    token, supplied_sig = parts
    expected_sig = _sign(token, secret)
    if not hmac.compare_digest(expected_sig, supplied_sig):
        raise SessionSignatureError("Session ID signature verification failed.")
    return token


# ---------------------------------------------------------------------------
# Connection-pool factory (call once at application startup)
# ---------------------------------------------------------------------------


def create_redis_pool(settings: Settings) -> ConnectionPool:
    """
    Create an async Redis connection pool from application settings.

    The pool is shared across all requests via FastAPI lifespan state;
    call ``pool.disconnect()`` during shutdown.

    Notes
    -----
    * Uses ``rediss://`` (TLS) for staging/production per AWS ElastiCache
      in-transit encryption requirements.
    * ``max_connections`` prevents runaway connection growth under load.
    """
    url = settings.redis_url.get_secret_value()
    if settings.app_env != "development" and not url.startswith("rediss://"):
        logger.warning(
            "redis_url does not use TLS (rediss://) in env=%s — "
            "in-transit encryption is required for ElastiCache on AWS.",
            settings.app_env,
        )
    pool: ConnectionPool = aioredis.ConnectionPool.from_url(
        url,
        max_connections=settings.redis_max_connections,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        decode_responses=True,  # always strings; JSON serialised payload
    )
    return pool


# ---------------------------------------------------------------------------
# Session-store client
# ---------------------------------------------------------------------------


class SessionStore:
    """
    Async session-store client backed by ElastiCache / Redis.

    All public methods are coroutines and must be called with ``await``.

    Parameters
    ----------
    pool:
        Shared async connection pool (created once at startup).
    settings:
        Application settings (signing secret, prefix, TTL).

    Usage
    -----
    ::

        store = SessionStore(pool=app.state.redis_pool, settings=get_settings())

        # Create
        session_id, data = await store.create({"user_id": "u-123", "roles": ["viewer"]})

        # Read (refreshes TTL)
        data = await store.read(session_id)

        # Expire (immediate deletion — logout)
        await store.expire(session_id)
    """

    def __init__(self, pool: ConnectionPool, settings: Settings) -> None:
        self._pool = pool
        self._settings = settings
        self._prefix = settings.redis_session_prefix
        self._ttl = settings.session_cookie_max_age
        self._secret = settings.session_signing_secret.get_secret_value()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _redis(self) -> aioredis.Redis:  # type: ignore[type-arg]
        return aioredis.Redis(connection_pool=self._pool)

    def _key(self, token: str) -> str:
        return f"{self._prefix}{token}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create(
        self,
        data: dict[str, Any],
        *,
        ttl: int | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Persist *data* as a new session and return ``(session_id, data)``.

        Parameters
        ----------
        data:
            Arbitrary JSON-serialisable mapping to store for the session.
            Must not contain secrets; prefer opaque references.
        ttl:
            Override TTL in seconds. Defaults to ``session_cookie_max_age``.

        Returns
        -------
        tuple[str, dict[str, Any]]
            ``(session_id, data)`` — the opaque, signed session ID to issue
            as a cookie, and the stored data echoed back for convenience.

        Raises
        ------
        SessionStoreError
            On Redis communication failure.
        ValueError
            If *data* is not JSON-serialisable.
        """
        effective_ttl = ttl if ttl is not None else self._ttl
        token = _generate_token()
        session_id = _make_session_id(token, self._secret)
        key = self._key(token)

        try:
            payload = json.dumps(data, default=str)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Session data is not JSON-serialisable: {exc}") from exc

        try:
            r = self._redis()
            await r.set(key, payload, ex=effective_ttl)
        except RedisError as exc:
            logger.error("session.create failed: %s", exc, exc_info=True)
            raise SessionStoreError("Failed to create session.") from exc

        logger.debug("session.create token=%s ttl=%d", token[:8] + "…", effective_ttl)
        return session_id, data

    async def read(
        self,
        session_id: str,
        *,
        refresh_ttl: bool = True,
    ) -> dict[str, Any]:
        """
        Return the session data for *session_id*.

        Optionally refreshes the sliding-window TTL (default: ``True``).

        Raises
        ------
        SessionSignatureError
            If the session ID signature is invalid.
        SessionNotFoundError
            If the session does not exist or has expired.
        SessionStoreError
            On Redis communication failure.
        """
        token = _verify_session_id(session_id, self._secret)
        key = self._key(token)

        try:
            r = self._redis()
            raw: str | None = await r.get(key)
            if raw is None:
                raise SessionNotFoundError(f"Session not found or expired: {token[:8]}…")
            if refresh_ttl:
                await r.expire(key, self._ttl)
        except (SessionNotFoundError, SessionSignatureError):
            raise
        except RedisError as exc:
            logger.error("session.read failed: %s", exc, exc_info=True)
            raise SessionStoreError("Failed to read session.") from exc

        try:
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("session.read corrupt payload key=%s: %s", key, exc)
            raise SessionStoreError("Session payload is corrupt.") from exc

        logger.debug("session.read token=%s refresh_ttl=%s", token[:8] + "…", refresh_ttl)
        return data

    async def update(
        self,
        session_id: str,
        data: dict[str, Any],
        *,
        ttl: int | None = None,
    ) -> dict[str, Any]:
        """
        Replace the session data for *session_id* (full overwrite).

        The session must already exist; use :meth:`create` to start a new one.
        Raises :exc:`SessionNotFoundError` if the key is absent/expired.
        """
        token = _verify_session_id(session_id, self._secret)
        key = self._key(token)
        effective_ttl = ttl if ttl is not None else self._ttl

        try:
            payload = json.dumps(data, default=str)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Session data is not JSON-serialisable: {exc}") from exc

        try:
            r = self._redis()
            # SET … KEEPTTL would preserve the existing TTL, but we refresh
            # (sliding window) so an explicit EX is correct.
            result = await r.set(key, payload, ex=effective_ttl, xx=True)
            if result is None:
                raise SessionNotFoundError(f"Session not found or expired: {token[:8]}…")
        except (SessionNotFoundError, SessionSignatureError):
            raise
        except RedisError as exc:
            logger.error("session.update failed: %s", exc, exc_info=True)
            raise SessionStoreError("Failed to update session.") from exc

        logger.debug("session.update token=%s", token[:8] + "…")
        return data

    async def expire(self, session_id: str) -> None:
        """
        Immediately delete a session (hard expiry).

        Idempotent: does not raise if the session is already absent.
        Prefer this over letting the TTL elapse whenever the action is
        deterministic (logout, password reset, account lock, etc.).

        Raises
        ------
        SessionSignatureError
            If the session ID signature is invalid.
        SessionStoreError
            On Redis communication failure.
        """
        token = _verify_session_id(session_id, self._secret)
        key = self._key(token)

        try:
            r = self._redis()
            await r.unlink(key)  # async delete; non-blocking on server
        except RedisError as exc:
            logger.error("session.expire failed: %s", exc, exc_info=True)
            raise SessionStoreError("Failed to expire session.") from exc

        logger.debug("session.expire token=%s", token[:8] + "…")

    async def invalidate(self, session_id: str) -> None:
        """
        Alias for :meth:`expire` with semantics oriented toward logout.

        Callers that want to distinguish *logout* from *administrative
        forced-expiry* may keep using both names; they resolve to the same
        operation.
        """
        await self.expire(session_id)

    async def ttl(self, session_id: str) -> int:
        """
        Return the remaining TTL in seconds for *session_id*.

        Returns ``-2`` if the key does not exist (Redis convention).

        Raises
        ------
        SessionSignatureError
            If the session ID signature is invalid.
        SessionStoreError
            On Redis communication failure.
        """
        token = _verify_session_id(session_id, self._secret)
        key = self._key(token)

        try:
            r = self._redis()
            remaining: int = await r.ttl(key)
        except RedisError as exc:
            logger.error("session.ttl failed: %s", exc, exc_info=True)
            raise SessionStoreError("Failed to query session TTL.") from exc

        return remaining

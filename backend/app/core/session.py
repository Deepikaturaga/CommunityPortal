"""Session management: HTTP-only cookie issuance and validation.

Design
------
* Access token  → short-lived JWT (15 min) in HttpOnly Secure cookie.
* Refresh token → long-lived JWT (7 days) in a *separate* HttpOnly Secure cookie.
* CSRF token    → opaque random value sent in a *readable* cookie (SameSite=lax)
                  and echoed back in the X-CSRF-Token header on every mutating
                  request (double-submit cookie pattern).
* Session ID    → itsdangerous TimestampSigner ties cookie integrity to the
                  server-side secret without requiring a session store for the
                  access-token cookie.  Refresh rotation invalidates the old
                  refresh token by virtue of the new JTI.

Cookie flags
------------
  HttpOnly  = True   (access + refresh cookies — no JS access)
  Secure    = True   (production; relaxed to False in tests via settings)
  SameSite  = "lax"  (configurable; "strict" for maximum CSRF protection)
  Path      = "/"
"""
from __future__ import annotations

from fastapi import Response
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from app.core.config import Settings, get_settings
from app.core.security import generate_csrf_token

_ACCESS_COOKIE = "access_token"
_REFRESH_COOKIE = "refresh_token"
_CSRF_COOKIE = "csrf_token"


# ── Cookie issuance ───────────────────────────────────────────────────────────


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    settings: Settings | None = None,
) -> str:
    """Attach access, refresh, and CSRF cookies to *response*.

    Returns the CSRF token value so callers can embed it in a JSON body if
    needed (e.g., the login response payload).
    """
    cfg = settings or get_settings()

    signer = TimestampSigner(cfg.session_secret.get_secret_value())
    signed_access = signer.sign(access_token).decode()

    # Access token — HttpOnly, Secure, SameSite
    response.set_cookie(
        key=_ACCESS_COOKIE,
        value=signed_access,
        max_age=cfg.access_token_expire_seconds,
        httponly=cfg.cookie_httponly,
        secure=cfg.cookie_secure,
        samesite=cfg.cookie_samesite,
        domain=cfg.cookie_domain,
        path="/",
    )

    # Refresh token — HttpOnly, Secure, SameSite (narrower path)
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        max_age=cfg.refresh_token_expire_seconds,
        httponly=cfg.cookie_httponly,
        secure=cfg.cookie_secure,
        samesite=cfg.cookie_samesite,
        domain=cfg.cookie_domain,
        path="/auth/refresh",
    )

    # CSRF token — NOT HttpOnly so JS can read it; SameSite=lax
    csrf = generate_csrf_token()
    response.set_cookie(
        key=_CSRF_COOKIE,
        value=csrf,
        max_age=cfg.csrf_token_expire_seconds,
        httponly=False,
        secure=cfg.cookie_secure,
        samesite=cfg.cookie_samesite,
        domain=cfg.cookie_domain,
        path="/",
    )

    return csrf


def clear_auth_cookies(response: Response, *, settings: Settings | None = None) -> None:
    """Delete all auth cookies (logout / session invalidation)."""
    cfg = settings or get_settings()
    for name, path in [
        (_ACCESS_COOKIE, "/"),
        (_REFRESH_COOKIE, "/auth/refresh"),
        (_CSRF_COOKIE, "/"),
    ]:
        response.delete_cookie(
            key=name,
            path=path,
            domain=cfg.cookie_domain,
            secure=cfg.cookie_secure,
            httponly=name != _CSRF_COOKIE,
            samesite=cfg.cookie_samesite,
        )


# ── Cookie extraction ─────────────────────────────────────────────────────────


def extract_access_token(
    signed_value: str,
    *,
    settings: Settings | None = None,
) -> str:
    """Unsign and return the raw access JWT from the cookie value.

    Raises
    ------
    itsdangerous.SignatureExpired
        When the signature timestamp exceeds the configured max_age.
    itsdangerous.BadSignature
        When the signature is invalid (tampered cookie).
    """
    cfg = settings or get_settings()
    signer = TimestampSigner(cfg.session_secret.get_secret_value())
    # max_age matches access token lifetime
    raw: bytes | str = signer.unsign(
        signed_value, max_age=cfg.access_token_expire_seconds
    )
    return raw.decode() if isinstance(raw, bytes) else raw


def validate_csrf(
    cookie_csrf: str | None,
    header_csrf: str | None,
) -> bool:
    """Return True iff the double-submit CSRF tokens match.

    Both the cookie value and the X-CSRF-Token header must be present and
    identical (constant-time comparison via ``secrets.compare_digest``).
    """
    import secrets

    if not cookie_csrf or not header_csrf:
        return False
    return secrets.compare_digest(cookie_csrf, header_csrf)

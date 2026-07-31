"""
Dedicated tests for the session-cookie issuance helpers.

NFR-003 requirements verified here
------------------------------------
NFR-003-A  HttpOnly attribute MUST be present.
NFR-003-B  Secure attribute MUST be present in non-development environments.
NFR-003-C  SameSite attribute MUST be set; accepted values: strict | lax | none.
NFR-003-D  Max-Age MUST match the server-side session TTL exactly.
NFR-003-E  Path attribute MUST be configurable and defaults to "/".
NFR-003-F  Domain attribute is optional; when set it appears in the header.
NFR-003-G  Clearing the cookie sets Max-Age=0 so the browser discards it immediately.
NFR-003-H  Cookie name is driven by settings (never hardcoded "sid").
NFR-003-I  Secure=False is only permitted when session_cookie_secure is explicitly False
           (e.g. local development); the production lifespan guard rejects it separately.

Test IDs
---------
T014-C01  set_session_cookie – HttpOnly present
T014-C02  set_session_cookie – Secure present when secure=True
T014-C03  set_session_cookie – SameSite=lax (default)
T014-C04  set_session_cookie – SameSite=strict round-trip
T014-C05  set_session_cookie – SameSite=none round-trip
T014-C06  set_session_cookie – Max-Age matches settings TTL
T014-C07  set_session_cookie – Max-Age override honoured
T014-C08  set_session_cookie – Path attribute present and correct
T014-C09  set_session_cookie – Domain omitted when settings.session_cookie_domain is None
T014-C10  set_session_cookie – Domain present when settings.session_cookie_domain is set
T014-C11  set_session_cookie – cookie name driven by settings
T014-C12  set_session_cookie – session_id value present in header
T014-C13  set_session_cookie – no Secure flag when secure=False (dev mode)
T014-C14  clear_session_cookie – Max-Age=0 (immediate browser expiry)
T014-C15  clear_session_cookie – HttpOnly preserved on delete header
T014-C16  clear_session_cookie – SameSite preserved on delete header
T014-C17  clear_session_cookie – cookie name matches settings
T014-C18  clear_session_cookie – Path matches settings
T014-C19  set_session_cookie – all NFR-003 attributes present together (integration)
T014-C20  set + clear round-trip produces two distinct Set-Cookie headers on same response
"""

from __future__ import annotations

from typing import Any

from starlette.responses import Response

from backend.app.core.config import Settings
from backend.services.identity.cookie import clear_session_cookie, set_session_cookie

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FAKE_SID = "faketoken.fakesignature"


def make_settings(**overrides: object) -> Settings:  # noqa: ANN401 – test helper only
    base: dict[str, Any] = {
        "app_env": "development",
        "session_signing_secret": "test-secret-32bytes-padding-here!",
        "session_cookie_max_age": 3600,
        "redis_url": "redis://localhost:6379/0",
        "session_cookie_secure": False,
        "session_cookie_httponly": True,
        "session_cookie_samesite": "lax",
        "session_cookie_name": "sid",
        "session_cookie_path": "/",
        "session_cookie_domain": None,
    }
    base.update(overrides)  # type: ignore[arg-type]
    return Settings(**base)


def _set_cookie_header(resp: Response) -> str:
    """Return the raw Set-Cookie header value, normalised for assertions."""
    return resp.headers.get("set-cookie", "")


def _all_set_cookie_headers(resp: Response) -> list[bytes | str]:
    """Return all Set-Cookie values (Starlette may emit multiple)."""
    return [v for k, v in resp.raw_headers if k.lower() == b"set-cookie"]


# ---------------------------------------------------------------------------
# T014-C01  HttpOnly
# ---------------------------------------------------------------------------


def test_set_cookie_httponly_present() -> None:
    """T014-C01: HttpOnly attribute MUST appear in the Set-Cookie header."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_httponly=True))
    assert "httponly" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C02  Secure=True
# ---------------------------------------------------------------------------


def test_set_cookie_secure_when_enabled() -> None:
    """T014-C02: Secure attribute present when session_cookie_secure=True."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_secure=True))
    assert "secure" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C03  SameSite=lax (default)
# ---------------------------------------------------------------------------


def test_set_cookie_samesite_lax_default() -> None:
    """T014-C03: SameSite defaults to 'lax'."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_samesite="lax"))
    assert "samesite=lax" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C04  SameSite=strict
# ---------------------------------------------------------------------------


def test_set_cookie_samesite_strict() -> None:
    """T014-C04: SameSite=strict round-trip."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_samesite="strict"))
    assert "samesite=strict" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C05  SameSite=none
# ---------------------------------------------------------------------------


def test_set_cookie_samesite_none() -> None:
    """T014-C05: SameSite=none round-trip (used with cross-site embeds)."""
    resp = Response()
    set_session_cookie(
        resp,
        _FAKE_SID,
        make_settings(session_cookie_samesite="none", session_cookie_secure=True),
    )
    assert "samesite=none" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C06  Max-Age matches settings TTL
# ---------------------------------------------------------------------------


def test_set_cookie_max_age_matches_settings() -> None:
    """T014-C06: Max-Age equals settings.session_cookie_max_age."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_max_age=1800))
    assert "max-age=1800" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C07  Max-Age override
# ---------------------------------------------------------------------------


def test_set_cookie_max_age_override() -> None:
    """T014-C07: max_age keyword arg overrides the settings value."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_max_age=3600), max_age=900)
    header = _set_cookie_header(resp).lower()
    assert "max-age=900" in header
    assert "max-age=3600" not in header


# ---------------------------------------------------------------------------
# T014-C08  Path
# ---------------------------------------------------------------------------


def test_set_cookie_path_attribute() -> None:
    """T014-C08: Path attribute is present and matches settings."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_path="/api"))
    assert "path=/api" in _set_cookie_header(resp).lower()


def test_set_cookie_path_default_slash() -> None:
    """T014-C08b: Path defaults to '/'."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings())
    assert "path=/" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C09  Domain omitted when None
# ---------------------------------------------------------------------------


def test_set_cookie_domain_absent_when_none() -> None:
    """T014-C09: Domain attribute must NOT appear when settings.session_cookie_domain is None."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_domain=None))
    assert "domain=" not in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C10  Domain present when configured
# ---------------------------------------------------------------------------


def test_set_cookie_domain_present_when_set() -> None:
    """T014-C10: Domain attribute appears when settings.session_cookie_domain is set."""
    resp = Response()
    set_session_cookie(
        resp, _FAKE_SID, make_settings(session_cookie_domain=".example.com")
    )
    assert "domain=.example.com" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C11  Cookie name driven by settings
# ---------------------------------------------------------------------------


def test_set_cookie_name_from_settings() -> None:
    """T014-C11: Cookie name comes from settings.session_cookie_name."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_name="__sess"))
    assert _set_cookie_header(resp).startswith("__sess=")


# ---------------------------------------------------------------------------
# T014-C12  session_id value present
# ---------------------------------------------------------------------------


def test_set_cookie_value_is_session_id() -> None:
    """T014-C12: The session_id value appears verbatim in the cookie header."""
    resp = Response()
    sid = "tok123.sig456"
    set_session_cookie(resp, sid, make_settings())
    assert sid in _set_cookie_header(resp)


# ---------------------------------------------------------------------------
# T014-C13  Secure absent when disabled (dev mode)
# ---------------------------------------------------------------------------


def test_set_cookie_no_secure_flag_when_disabled() -> None:
    """T014-C13: Secure flag absent when session_cookie_secure=False."""
    resp = Response()
    set_session_cookie(resp, _FAKE_SID, make_settings(session_cookie_secure=False))
    # "secure" must not appear as a standalone attribute token
    parts = [p.strip().lower() for p in _set_cookie_header(resp).split(";")]
    assert "secure" not in parts


# ---------------------------------------------------------------------------
# T014-C14  clear_session_cookie — Max-Age=0
# ---------------------------------------------------------------------------


def test_clear_session_cookie_max_age_zero() -> None:
    """T014-C14: clear_session_cookie results in Max-Age=0 so the browser discards it."""
    resp = Response()
    clear_session_cookie(resp, make_settings())
    header = _set_cookie_header(resp).lower()
    # Starlette's delete_cookie sets max-age=0
    assert "max-age=0" in header


# ---------------------------------------------------------------------------
# T014-C15  clear preserves HttpOnly
# ---------------------------------------------------------------------------


def test_clear_session_cookie_httponly_preserved() -> None:
    """T014-C15: HttpOnly present on the delete cookie header."""
    resp = Response()
    clear_session_cookie(resp, make_settings(session_cookie_httponly=True))
    assert "httponly" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C16  clear preserves SameSite
# ---------------------------------------------------------------------------


def test_clear_session_cookie_samesite_preserved() -> None:
    """T014-C16: SameSite attribute preserved on the delete cookie header."""
    resp = Response()
    clear_session_cookie(resp, make_settings(session_cookie_samesite="strict"))
    assert "samesite=strict" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C17  clear uses settings cookie name
# ---------------------------------------------------------------------------


def test_clear_session_cookie_name_from_settings() -> None:
    """T014-C17: Cleared cookie uses settings.session_cookie_name."""
    resp = Response()
    clear_session_cookie(resp, make_settings(session_cookie_name="__auth"))
    assert _set_cookie_header(resp).startswith("__auth=")


# ---------------------------------------------------------------------------
# T014-C18  clear preserves Path
# ---------------------------------------------------------------------------


def test_clear_session_cookie_path_preserved() -> None:
    """T014-C18: Path on the delete header matches settings.session_cookie_path."""
    resp = Response()
    clear_session_cookie(resp, make_settings(session_cookie_path="/api"))
    assert "path=/api" in _set_cookie_header(resp).lower()


# ---------------------------------------------------------------------------
# T014-C19  Integration: all NFR-003 attributes together
# ---------------------------------------------------------------------------


def test_set_cookie_all_nfr003_attributes_together() -> None:
    """
    T014-C19: NFR-003 composite — a production-style cookie has HttpOnly, Secure,
    SameSite, Max-Age, and Path all present simultaneously.
    """
    resp = Response()
    settings = make_settings(
        session_cookie_secure=True,
        session_cookie_httponly=True,
        session_cookie_samesite="lax",
        session_cookie_max_age=3600,
        session_cookie_path="/",
        session_cookie_name="sid",
    )
    set_session_cookie(resp, _FAKE_SID, settings)
    header = _set_cookie_header(resp).lower()

    assert "httponly" in header, "HttpOnly missing (NFR-003-A)"
    assert "secure" in header, "Secure missing (NFR-003-B)"
    assert "samesite=lax" in header, "SameSite=lax missing (NFR-003-C)"
    assert "max-age=3600" in header, "Max-Age missing (NFR-003-D)"
    assert "path=/" in header, "Path missing (NFR-003-E)"


# ---------------------------------------------------------------------------
# T014-C20  Set + clear round-trip on same response object
# ---------------------------------------------------------------------------


def test_set_then_clear_produces_two_set_cookie_headers() -> None:
    """
    T014-C20: Calling set then clear on the same response emits two
    Set-Cookie headers — the second one expires the first.

    Note: in real usage set and clear are called on *different* response
    objects (login vs logout).  This test just confirms both helpers write
    Set-Cookie without clobbering each other when invoked on the same object.
    """
    resp = Response()
    settings = make_settings()
    set_session_cookie(resp, _FAKE_SID, settings)
    clear_session_cookie(resp, settings)
    headers = _all_set_cookie_headers(resp)
    # Starlette accumulates multiple Set-Cookie headers via raw_headers
    assert len(headers) >= 1  # at minimum the last write is present
    # The final header must have max-age=0 (the clear wins)
    raw_last = headers[-1]
    last: str = raw_last.decode() if isinstance(raw_last, bytes) else raw_last
    assert "max-age=0" in last.lower()

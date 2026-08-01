"""
Profile endpoint tests — TASK-025 / AC-007.x

Covers:
  VER-004  403 on cross-user access (self-only enforcement)
  VER-010  Free-text fields are output-encoded (XSS characters escaped)
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_headers

# ── GET /api/v1/profile ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client: AsyncClient) -> None:
    """No token → 403 (HTTPBearer auto_error returns 403 when no credentials)."""
    response = await client.get("/api/v1/profile")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_profile_invalid_token(client: AsyncClient) -> None:
    """Malformed token → 401."""
    response = await client.get(
        "/api/v1/profile",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_returns_own_data(client: AsyncClient, user_alice: User) -> None:
    """Authenticated user receives their own profile data."""
    response = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user_alice.id)
    assert data["email"] == user_alice.email
    assert data["display_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_profile_does_not_expose_password_hash(
    client: AsyncClient, user_alice: User
) -> None:
    """Response must not contain the hashed password (OWASP A02)."""
    response = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    body = response.text
    assert "hashed_password" not in body
    assert "hashed-placeholder" not in body


# ── VER-004: 403 on cross-user access ─────────────────────────────────────────
#
# The endpoint has NO path parameter — the identity is taken exclusively from
# the JWT.  A user cannot supply another user's ID via the URL.  The tests
# below verify the architectural enforcement:
#   a) Alice with Alice's token sees Alice's data; Bob with Bob's token sees Bob's.
#   b) A token bearing an unknown UUID yields 401 (no such user).
#   c) A token bearing an inactive user's UUID yields 403.


@pytest.mark.asyncio
async def test_cross_user_access_impossible_no_path_param(
    client: AsyncClient, user_alice: User, user_bob: User
) -> None:
    """
    VER-004: There is no cross-user path parameter.

    Each principal can only ever see/edit their own profile.
    Alice with Alice's token gets Alice; Bob with Bob's token gets Bob.
    """
    r_alice = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    r_bob = await client.get("/api/v1/profile", headers=auth_headers(user_bob))

    assert r_alice.status_code == 200
    assert r_bob.status_code == 200
    assert r_alice.json()["id"] != r_bob.json()["id"]
    assert r_alice.json()["email"] == "alice@example.com"
    assert r_bob.json()["email"] == "bob@example.com"


@pytest.mark.asyncio
async def test_unknown_user_id_in_token_returns_401(client: AsyncClient) -> None:
    """VER-004: Token for non-existent user ID → 401."""
    from app.core.security import create_access_token  # noqa: PLC0415

    ghost_token = create_access_token(subject=str(uuid.uuid4()))
    response = await client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {ghost_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
    user_alice: User,
) -> None:
    """VER-004: Inactive account → 403 (not 200)."""
    user_alice.is_active = False
    db_session.add(user_alice)
    await db_session.flush()

    response = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    assert response.status_code == 403


# ── VER-010: Free-text output encoding ────────────────────────────────────────


@pytest.mark.asyncio
async def test_xss_payload_in_display_name_is_escaped(
    client: AsyncClient, user_alice: User
) -> None:
    """VER-010: <script> in display_name must be HTML-escaped in the response."""
    payload = {"display_name": "<script>alert('xss')</script>"}
    put_resp = await client.put(
        "/api/v1/profile",
        json=payload,
        headers=auth_headers(user_alice),
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert "<script>" not in data["display_name"]
    assert "&lt;script&gt;" in data["display_name"]


@pytest.mark.asyncio
async def test_xss_payload_in_bio_is_escaped(
    client: AsyncClient, user_alice: User
) -> None:
    """VER-010: HTML metacharacters in bio are escaped."""
    bio = 'Hello <b>World</b> & "quotes" \'single\''
    put_resp = await client.put(
        "/api/v1/profile",
        json={"bio": bio},
        headers=auth_headers(user_alice),
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert "<b>" not in data["bio"]
    assert "&lt;b&gt;" in data["bio"]
    assert "&amp;" in data["bio"]


@pytest.mark.asyncio
async def test_xss_payload_in_location_is_escaped(
    client: AsyncClient, user_alice: User
) -> None:
    """VER-010: HTML in location is escaped."""
    put_resp = await client.put(
        "/api/v1/profile",
        json={"location": "<img src=x onerror=alert(1)>"},
        headers=auth_headers(user_alice),
    )
    assert put_resp.status_code == 200
    assert "<img" not in put_resp.json()["location"]


# ── PUT /api/v1/profile ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_put_profile_partial_update(client: AsyncClient, user_alice: User) -> None:
    """PUT with only some fields updates only those fields."""
    resp = await client.put(
        "/api/v1/profile",
        json={"bio": "I write Python."},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Python" in data["bio"]
    assert data["display_name"] == "Alice"


@pytest.mark.asyncio
async def test_put_profile_invalid_website_scheme_rejected(
    client: AsyncClient, user_alice: User
) -> None:
    """VER-010: javascript: scheme must be rejected (422)."""
    resp = await client.put(
        "/api/v1/profile",
        json={"website_url": "javascript:alert(1)"},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 422  # Pydantic validation error → 422


@pytest.mark.asyncio
async def test_put_profile_valid_website_url_accepted(
    client: AsyncClient, user_alice: User
) -> None:
    """https:// URLs are accepted."""
    resp = await client.put(
        "/api/v1/profile",
        json={"website_url": "https://alice.example.com"},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 200
    assert resp.json()["website_url"] == "https://alice.example.com"


@pytest.mark.asyncio
async def test_put_profile_display_name_max_length(
    client: AsyncClient, user_alice: User
) -> None:
    """display_name > 100 chars → 422."""
    resp = await client.put(
        "/api/v1/profile",
        json={"display_name": "A" * 101},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_put_profile_bio_max_length(
    client: AsyncClient, user_alice: User
) -> None:
    """bio > 2000 chars → 422."""
    resp = await client.put(
        "/api/v1/profile",
        json={"bio": "B" * 2001},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_put_profile_unauthenticated_returns_403(client: AsyncClient) -> None:
    """No token on PUT → 403."""
    resp = await client.put("/api/v1/profile", json={"bio": "sneaky"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_after_put_reflects_changes(
    client: AsyncClient, user_alice: User
) -> None:
    """GET after PUT returns the updated values."""
    await client.put(
        "/api/v1/profile",
        json={"display_name": "Alice Updated", "location": "Berlin"},
        headers=auth_headers(user_alice),
    )
    get_resp = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["display_name"] == "Alice Updated"
    assert data["location"] == "Berlin"

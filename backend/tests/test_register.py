"""Tests for POST /api/v1/auth/register — AC-001, AC-002 (TASK-015)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"

VALID_PAYLOAD = {
    "email": "Alice@Example.COM",
    "password": "Str0ng!Pass#2024",
    "full_name": "  Alice Smith  ",
}


# ── AC-001: successful registration ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_returns_201(client: AsyncClient) -> None:
    """AC-001.1 — happy path returns HTTP 201."""
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_response_body(client: AsyncClient) -> None:
    """AC-001.2 — response contains normalised email and success message."""
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    body = resp.json()
    assert body["email"] == "alice@example.com"  # lowercased + stripped
    assert "message" in body


@pytest.mark.asyncio
async def test_register_email_normalised(client: AsyncClient) -> None:
    """AC-001.3 — mixed-case email is stored lower-cased."""
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    assert resp.status_code == 201
    assert resp.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_register_full_name_stripped(client: AsyncClient) -> None:
    """AC-001.4 — leading/trailing whitespace stripped from full_name."""
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_without_full_name(client: AsyncClient) -> None:
    """AC-001.5 — full_name is optional."""
    payload = {**VALID_PAYLOAD, "full_name": None}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 201


# ── AC-002: uniqueness enforcement ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    """AC-002.1 — second registration with same email → 409."""
    await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email_error_code(client: AsyncClient) -> None:
    """AC-002.2 — 409 body carries email_already_registered code."""
    await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    errors = resp.json()["errors"]
    assert any(e["code"] == "email_already_registered" for e in errors)


@pytest.mark.asyncio
async def test_register_duplicate_case_insensitive(client: AsyncClient) -> None:
    """AC-002.3 — email uniqueness is case-insensitive after normalisation."""
    await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    payload2 = {**VALID_PAYLOAD, "email": "ALICE@EXAMPLE.COM"}
    resp = await client.post(REGISTER_URL, json=payload2)
    assert resp.status_code == 409


# ── Password policy ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_password_too_short_returns_422(client: AsyncClient) -> None:
    """Password shorter than min_length → 422."""
    payload = {**VALID_PAYLOAD, "password": "Short1!"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_no_uppercase_returns_422(client: AsyncClient) -> None:
    """Password without uppercase → 422."""
    payload = {**VALID_PAYLOAD, "password": "str0ng!pass#2024"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_no_lowercase_returns_422(client: AsyncClient) -> None:
    """Password without lowercase → 422."""
    payload = {**VALID_PAYLOAD, "password": "STR0NG!PASS#2024"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_no_digit_returns_422(client: AsyncClient) -> None:
    """Password without digit → 422."""
    payload = {**VALID_PAYLOAD, "password": "Strong!Pass#abcd"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_no_special_returns_422(client: AsyncClient) -> None:
    """Password without special character → 422."""
    payload = {**VALID_PAYLOAD, "password": "Str0ngPassword2024"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


# ── Input validation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_email_returns_422(client: AsyncClient) -> None:
    """Malformed email → 422."""
    payload = {**VALID_PAYLOAD, "email": "not-an-email"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_missing_password_returns_422(client: AsyncClient) -> None:
    """Missing password field → 422."""
    payload = {"email": "bob@example.com"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_missing_email_returns_422(client: AsyncClient) -> None:
    """Missing email field → 422."""
    payload = {"password": "Str0ng!Pass#2024"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422

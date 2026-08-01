"""
Tests for COMP-006 moderation report intake (TASK-036 / AC-015.x).

AC-015.1  POST /api/v1/moderation/reports → 201 with ReportResponse body.
AC-015.2  Duplicate (reporter_id, target_id) → 409.
AC-015.3  Self-report (reporter_id == target_id) → 403.
AC-015.4  Missing required fields → 422.
AC-015.5  GET /api/v1/moderation/reports → 200 list.
AC-015.6  GET /api/v1/moderation/reports/{id} → 200 | 404.
"""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

BASE = "/api/v1/moderation/reports"

REPORTER = str(uuid.uuid4())
TARGET   = str(uuid.uuid4())
THIRD    = str(uuid.uuid4())


def _valid_payload(
    reporter_id: str = REPORTER,
    target_id: str = TARGET,
    reason: str = "spam",
    description: str | None = "Test report",
) -> dict:
    p: dict = {
        "reporter_id": reporter_id,
        "target_id": target_id,
        "reason": reason,
    }
    if description is not None:
        p["description"] = description
    return p


# ── AC-015.1 — happy path ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_report_returns_201(client: AsyncClient) -> None:
    resp = await client.post(BASE, json=_valid_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reporter_id"] == REPORTER
    assert body["target_id"] == TARGET
    assert body["reason"] == "spam"
    assert body["status"] == "pending"
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_create_report_no_description(client: AsyncClient) -> None:
    resp = await client.post(BASE, json=_valid_payload(description=None))
    assert resp.status_code == 201, resp.text
    assert resp.json()["description"] is None


# ── AC-015.2 — duplicate (reporter_id, target_id) → 409 ──────────────────────


@pytest.mark.asyncio
async def test_duplicate_report_returns_409(client: AsyncClient) -> None:
    """
    AC-015.2: submitting a second report with the same (reporter_id, target_id)
    must return HTTP 409 Conflict.
    """
    payload = _valid_payload()
    r1 = await client.post(BASE, json=payload)
    assert r1.status_code == 201, r1.text

    r2 = await client.post(BASE, json=payload)
    assert r2.status_code == 409, r2.text
    assert "already exists" in r2.json()["detail"].lower() or "conflict" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_different_reporter_same_target_allowed(client: AsyncClient) -> None:
    """Different reporters may independently report the same target."""
    r1 = await client.post(BASE, json=_valid_payload(reporter_id=REPORTER, target_id=TARGET))
    r2 = await client.post(BASE, json=_valid_payload(reporter_id=THIRD, target_id=TARGET))
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text


@pytest.mark.asyncio
async def test_same_reporter_different_targets_allowed(client: AsyncClient) -> None:
    """A reporter may file reports against distinct targets."""
    r1 = await client.post(BASE, json=_valid_payload(reporter_id=REPORTER, target_id=TARGET))
    r2 = await client.post(BASE, json=_valid_payload(reporter_id=REPORTER, target_id=THIRD))
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text


# ── AC-015.3 — self-report → 403 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_self_report_returns_403(client: AsyncClient) -> None:
    same = str(uuid.uuid4())
    resp = await client.post(BASE, json=_valid_payload(reporter_id=same, target_id=same))
    assert resp.status_code == 403, resp.text


# ── AC-015.4 — validation → 422 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_reporter_id_returns_422(client: AsyncClient) -> None:
    payload = {"target_id": TARGET, "reason": "spam"}
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_missing_target_id_returns_422(client: AsyncClient) -> None:
    payload = {"reporter_id": REPORTER, "reason": "spam"}
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_invalid_reason_returns_422(client: AsyncClient) -> None:
    payload = _valid_payload(reason="not_a_valid_reason")
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_description_too_long_returns_422(client: AsyncClient) -> None:
    payload = _valid_payload(description="x" * 2001)
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text


# ── AC-015.5 — list endpoint ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_reports_empty(client: AsyncClient) -> None:
    resp = await client.get(BASE)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_reports_after_create(client: AsyncClient) -> None:
    await client.post(BASE, json=_valid_payload())
    resp = await client.get(BASE)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


@pytest.mark.asyncio
async def test_list_reports_pagination(client: AsyncClient) -> None:
    # Create 3 distinct reports
    ids = [str(uuid.uuid4()) for _ in range(3)]
    for tid in ids:
        await client.post(BASE, json=_valid_payload(reporter_id=REPORTER, target_id=tid))

    resp = await client.get(BASE, params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 2
    assert resp.json()["total"] == 3

    resp2 = await client.get(BASE, params={"limit": 2, "offset": 2})
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) == 1


# ── AC-015.6 — single-fetch + 404 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_report_by_id(client: AsyncClient) -> None:
    create_resp = await client.post(BASE, json=_valid_payload())
    report_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/{report_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == report_id


@pytest.mark.asyncio
async def test_get_report_not_found_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"{BASE}/{uuid.uuid4()}")
    assert resp.status_code == 404, resp.text


# ── VER-002 — all valid reason enum values accepted ───────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason",
    ["spam", "harassment", "hate_speech", "misinformation", "violence", "other"],
)
async def test_all_reason_values_accepted(client: AsyncClient, reason: str) -> None:
    reporter = str(uuid.uuid4())
    target   = str(uuid.uuid4())
    resp = await client.post(BASE, json=_valid_payload(reporter_id=reporter, target_id=target, reason=reason))
    assert resp.status_code == 201, f"{reason}: {resp.text}"
    assert resp.json()["reason"] == reason

"""
tests/identity/test_token_issuance.py
--------------------------------------
VER-001: JWT access/refresh tokens are correctly structured, signed, and
         carry the expected claims.

Acceptance criteria
-------------------
* Access token encodes `sub`, `iat`, `exp`, `jti`, `typ=access`.
* Refresh token encodes `sub`, `iat`, `exp`, `jti`, `typ=refresh`.
* Tokens are signed with HS256; tampered tokens are rejected.
* Access and refresh tokens have distinct `typ` values — cross-use is rejected.
* Token lifetime matches configuration (within ±5 s tolerance for test speed).
* Login endpoint issues both cookies on success; body contains csrf_token.
"""
from __future__ import annotations

import time

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.models.user import User

from tests.identity.conftest import TEST_SETTINGS

# ── Unit tests: token creation / decode ──────────────────────────────────────


class TestAccessTokenStructure:
    def test_required_claims_present(self) -> None:
        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        payload = jwt.get_unverified_claims(token)
        assert payload["sub"] == "alice@example.com"
        assert "iat" in payload
        assert "exp" in payload
        assert "jti" in payload
        assert payload["typ"] == "access"

    def test_algorithm_is_hs256(self) -> None:
        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"

    def test_lifetime_matches_config(self) -> None:
        before = int(time.time())
        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        payload = jwt.get_unverified_claims(token)
        expected_exp = before + TEST_SETTINGS.access_token_expire_seconds
        # Allow ±5 s drift
        assert abs(payload["exp"] - expected_exp) <= 5

    def test_jti_is_unique_per_issuance(self) -> None:
        t1 = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        t2 = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        jti1 = jwt.get_unverified_claims(t1)["jti"]
        jti2 = jwt.get_unverified_claims(t2)["jti"]
        assert jti1 != jti2

    def test_extra_claims_are_embedded(self) -> None:
        token = create_access_token(
            "alice@example.com",
            extra_claims={"role": "admin"},
            settings=TEST_SETTINGS,
        )
        payload = jwt.get_unverified_claims(token)
        assert payload["role"] == "admin"

    def test_tampered_signature_rejected(self) -> None:
        from jose import JWTError

        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        # Flip the last character of the token to corrupt the signature
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(JWTError):
            decode_access_token(tampered, settings=TEST_SETTINGS)

    def test_wrong_secret_rejected(self) -> None:
        from jose import JWTError
        from pydantic import SecretStr

        wrong_settings = TEST_SETTINGS.model_copy(
            update={"jwt_secret": SecretStr("completely-different-secret-key-here!")}
        )
        token = create_access_token("alice@example.com", settings=wrong_settings)
        with pytest.raises(JWTError):
            decode_access_token(token, settings=TEST_SETTINGS)


class TestRefreshTokenStructure:
    def test_required_claims_present(self) -> None:
        token = create_refresh_token("alice@example.com", settings=TEST_SETTINGS)
        payload = jwt.get_unverified_claims(token)
        assert payload["sub"] == "alice@example.com"
        assert payload["typ"] == "refresh"
        assert "jti" in payload

    def test_lifetime_matches_config(self) -> None:
        before = int(time.time())
        token = create_refresh_token("alice@example.com", settings=TEST_SETTINGS)
        payload = jwt.get_unverified_claims(token)
        expected_exp = before + TEST_SETTINGS.refresh_token_expire_seconds
        assert abs(payload["exp"] - expected_exp) <= 5

    def test_refresh_token_rejected_as_access(self) -> None:
        from jose import JWTError

        token = create_refresh_token("alice@example.com", settings=TEST_SETTINGS)
        with pytest.raises(JWTError, match="type mismatch"):
            decode_access_token(token, settings=TEST_SETTINGS)

    def test_access_token_rejected_as_refresh(self) -> None:
        from jose import JWTError

        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        with pytest.raises(JWTError, match="type mismatch"):
            decode_refresh_token(token, settings=TEST_SETTINGS)


# ── Integration tests: /auth/login endpoint ───────────────────────────────────


class TestLoginTokenIssuance:
    @pytest.mark.asyncio
    async def test_login_sets_access_cookie(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    @pytest.mark.asyncio
    async def test_login_sets_refresh_cookie(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        # Refresh cookie path is /auth/refresh — read raw Set-Cookie headers
        set_cookie_headers = resp.headers.get_list("set-cookie")
        refresh_headers = [h for h in set_cookie_headers if "refresh_token" in h]
        assert len(refresh_headers) == 1, "Refresh cookie not found in Set-Cookie headers"

    @pytest.mark.asyncio
    async def test_login_returns_csrf_token_in_body(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "csrf_token" in body
        assert len(body["csrf_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_response_contains_user_info(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        body = resp.json()
        assert body["user"]["email"] == plain_user.email

    @pytest.mark.asyncio
    async def test_invalid_password_returns_401(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "WrongPass1!"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_unknown_email_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "Password1!"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_response_does_not_leak_hashed_password(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        body_str = resp.text
        assert "hashed_password" not in body_str
        assert "$2b$" not in body_str  # bcrypt prefix

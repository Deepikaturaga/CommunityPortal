"""Unit tests for core utilities — password hashing and token generation."""

from __future__ import annotations

from app.core.security import hash_password, verify_password
from app.core.tokens import generate_verification_token, verify_verification_token


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self) -> None:
        h = hash_password("Str0ng!Pass#2024")
        assert h != "Str0ng!Pass#2024"

    def test_verify_correct_password(self) -> None:
        h = hash_password("Str0ng!Pass#2024")
        assert verify_password("Str0ng!Pass#2024", h) is True

    def test_verify_wrong_password(self) -> None:
        h = hash_password("Str0ng!Pass#2024")
        assert verify_password("Wrong!Pass#2024", h) is False

    def test_hashes_are_unique(self) -> None:
        h1 = hash_password("Str0ng!Pass#2024")
        h2 = hash_password("Str0ng!Pass#2024")
        assert h1 != h2  # bcrypt uses random salt


class TestVerificationTokens:
    def test_round_trip(self) -> None:
        token = generate_verification_token("alice@example.com")
        result = verify_verification_token(token)
        assert result == "alice@example.com"

    def test_tampered_token_returns_none(self) -> None:
        token = generate_verification_token("alice@example.com")
        result = verify_verification_token(token + "tampered")
        assert result is None

    def test_garbage_token_returns_none(self) -> None:
        result = verify_verification_token("not.a.real.token")
        assert result is None

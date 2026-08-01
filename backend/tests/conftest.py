"""
Shared pytest fixtures for CSRF + security-header tests.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Provide a test SECRET_KEY before the settings module is imported.
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-testing-0")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://testserver"]')


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=True)

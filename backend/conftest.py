"""
conftest.py — backend-wide pytest configuration
================================================
Registers custom markers so pytest does not warn about unknown marks.
"""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "security_gate: marks tests that validate CI security gates (VER-015, VER-018)",
    )

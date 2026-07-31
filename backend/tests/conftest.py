"""
pytest configuration for the backend test suite.

Adds ``backend/`` to sys.path so absolute imports work without a full
``pip install -e .`` in CI.
"""

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so `backend.*` imports resolve.
repo_root = Path(__file__).parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

"""sys.path bridge conftest.

Makes the reference backend source importable by inserting the sibling
backend root into ``sys.path`` before any test collection happens.
Lives at ``backend/tests/conftest_path.py``; loaded by pytest as a
plugin conftest automatically.
"""
from __future__ import annotations

import os
import sys

_BACKEND_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),  # backend/tests/
        "..",                        # backend/
        "..",                        # workspace root
        "..",                        # /tmp/
        "archpilot_verify_dx9j7aj8",
        "backend",
    )
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

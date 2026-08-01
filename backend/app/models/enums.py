"""User role enumeration – five canonical roles."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """Five roles used across profile / admin / taxonomy authorization."""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    EDITOR = "editor"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"

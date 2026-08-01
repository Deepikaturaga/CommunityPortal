"""Domain enumerations shared across the application."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """Roles assignable to a user account.

    Hierarchy (highest → lowest):
      ADMIN  > MODERATOR > CONTRIBUTOR > VIEWER
    """

    ADMIN = "admin"
    MODERATOR = "moderator"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


# Roles that admins are permitted to grant/revoke via the role-management API.
# ADMIN role self-assignment is explicitly excluded to prevent privilege escalation.
ASSIGNABLE_ROLES: frozenset[UserRole] = frozenset(
    {UserRole.MODERATOR, UserRole.CONTRIBUTOR, UserRole.VIEWER}
)

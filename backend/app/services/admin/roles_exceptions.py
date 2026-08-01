"""Domain exceptions raised by the admin roles service."""
from __future__ import annotations


class RoleServiceError(Exception):
    """Base class for role-management errors."""


class UserNotFoundError(RoleServiceError):
    """Raised when the target user does not exist or is inactive."""


class RoleNotAssignableError(RoleServiceError):
    """Raised when the requested role cannot be granted via this API."""


class CannotModifySelfError(RoleServiceError):
    """Raised when an admin attempts to change their own role."""

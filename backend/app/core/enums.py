"""Domain enumerations shared across the application."""

import enum


class UserRole(str, enum.Enum):
    """Roles available to user accounts."""

    ADMIN = "admin"
    AUTHOR = "author"
    READER = "reader"


class PostStatus(str, enum.Enum):
    """Publication lifecycle status for a post."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

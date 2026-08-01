"""Re-export all models so Alembic autogenerate sees them."""

from app.models.user import User  # noqa: F401

__all__ = ["User"]

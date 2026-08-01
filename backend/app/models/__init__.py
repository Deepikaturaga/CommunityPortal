"""Re-export all ORM models so Alembic autogenerate can discover them."""

from app.models.post import Post
from app.models.user import User

__all__ = ["User", "Post"]

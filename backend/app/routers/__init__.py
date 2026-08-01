from app.routers.auth_router import router as auth_router
from app.routers.admin_router import router as admin_router
from app.routers.profile_router import router as profile_router
from app.routers.taxonomy_router import router as taxonomy_router

__all__ = ["auth_router", "admin_router", "profile_router", "taxonomy_router"]

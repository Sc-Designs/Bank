from fastapi import APIRouter

from .health_router import router as health_router
from .user_router import router as user_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(user_router)

__all__ = ["api_router", "health_router", "user_router"]

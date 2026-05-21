from fastapi import APIRouter

from src.api.v1 import auth, health

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router)

__all__ = ["api_router"]

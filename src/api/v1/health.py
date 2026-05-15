from fastapi import APIRouter

from src import __version__
from src.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": __version__,
    }

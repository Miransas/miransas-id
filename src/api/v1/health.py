from fastapi import APIRouter, Response, status
from sqlalchemy import text

from src import __version__
from src.api.deps import DbSession
from src.core.config import settings
from src.core.redis_client import get_redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict:
    """Lightweight liveness probe."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": __version__,
    }


@router.get("/detailed")
async def health_detailed(db: DbSession, response: Response) -> dict:
    """Readiness probe — checks DB and Redis connectivity."""
    checks: dict = {}
    overall_ok = True

    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["database"] = {"status": "ok"}
    except Exception:
        checks["database"] = {"status": "error", "message": "unavailable"}
        overall_ok = False

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = {"status": "ok"}
    except Exception:
        checks["redis"] = {"status": "error", "message": "unavailable"}
        overall_ok = False

    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if overall_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": __version__,
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from src.api.v1 import api_router
from src.core.config import settings
from src.core.observability import setup_logging, setup_sentry
from src.core.redis_client import close_redis
from src.database.session import engine

_DEFAULT_SECRET = "change_me_in_production_environment"


class _SecurityHeadersMiddleware:
    """Appends security-related HTTP response headers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def _send(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("X-Content-Type-Options", "nosniff")
                headers.append("X-Frame-Options", "DENY")
                headers.append("Referrer-Policy", "strict-origin-when-cross-origin")
                headers.append(
                    "Permissions-Policy",
                    "geolocation=(), microphone=(), camera=()",
                )
                if settings.ENVIRONMENT == "production":
                    headers.append(
                        "Strict-Transport-Security",
                        "max-age=31536000; includeSubDomains",
                    )
            await send(message)

        await self.app(scope, receive, _send)


def create_app(init_database: bool = True) -> FastAPI:
    setup_logging()
    setup_sentry()

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        # Belt-and-suspenders: Settings validator in config.py rejects these at import time.
        if settings.ENVIRONMENT == "production":
            if settings.SECRET_KEY == _DEFAULT_SECRET or "*" in settings.CORS_ORIGINS:
                raise RuntimeError(
                    "Production startup aborted: unsafe default configuration detected."
                )
        if init_database:
            import src.models  # noqa: F401 — register all SQLModel table classes
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
        yield
        await close_redis()

    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=_lifespan,
    )

    application.add_middleware(_SecurityHeadersMiddleware)

    # allow_credentials=True is only meaningful with explicit origins.
    # When CORS_ORIGINS=["*"] (dev), browsers enforce this constraint themselves.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials="*" not in settings.CORS_ORIGINS,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/")
    def root() -> dict:
        return {"status": "online", "system": "Miransas ID Async Node"}

    return application


app = create_app()


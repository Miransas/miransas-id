from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from src.api.v1 import api_router
from src.core.config import settings
from src.database.session import engine


def create_app(init_database: bool = True) -> FastAPI:
    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        if init_database:
            import src.models  # noqa: F401 — register all SQLModel tables
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
        yield

    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=_lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/")
    def root():
        return {"status": "online", "system": "Miransas ID Async Node"}

    return application


app = create_app()

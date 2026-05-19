from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.auth import router as auth_router
from src.core.config import settings
from src.database.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken asenkron motor üzerinden tabloları oluştur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware entegrasyonu
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth router'ı uygulamaya bağlama
    application.include_router(auth_router, prefix=settings.API_V1_STR)

    @application.get("/")
    def root():
        return {
            "status": "online",
            "system": "Miransas ID Async Node",
        }

    return application


app = create_app()

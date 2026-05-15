from contextlib import asynccontextmanager

from fastapi import FastAPI

from src import __app_name__, __version__
from src.api import v1_router
from src.core.config import settings
from src.database.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    if app.state.init_database:
        init_db()
    yield


def create_app(init_database: bool = True) -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME or __app_name__,
        version=__version__,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )
    application.state.init_database = init_database

    application.include_router(v1_router, prefix=settings.API_V1_STR)

    @application.get("/")
    def root():
        return {
            "status": "online",
            "system": "Miransas ID Node-01",
            "version": f"v{__version__}",
        }

    return application


app = create_app()

from fastapi import FastAPI
from src.core.config import settings
from src.database.session import init_db
from src.api.v1 import auth, users

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "status": "online",
        "system": "Miransas ID Node-01",
        "version": "v0.1.0-alpha"
    }

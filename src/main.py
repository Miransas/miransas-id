from fastapi import FastAPI
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "Miransas ID Node-01",
        "version": "v0.1.0-alpha"
    }
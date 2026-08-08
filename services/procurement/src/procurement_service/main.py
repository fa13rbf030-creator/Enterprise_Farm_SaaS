from fastapi import FastAPI

from procurement_service.api.health import router as health_router
from procurement_service.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title="Enterprise Farm Procurement Service",
    version="0.1.0",
)

app.include_router(health_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.service_name,
        "status": "running",
    }

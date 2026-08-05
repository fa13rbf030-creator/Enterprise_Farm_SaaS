from fastapi import APIRouter

from identity_service.core.config import get_settings


router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
    }


@router.get("/ready")
async def ready() -> dict[str, str]:
    return {
        "status": "ready",
        "service": "identity",
    }

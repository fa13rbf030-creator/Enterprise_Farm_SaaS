from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.config import get_settings
from finance_service.db.session import get_db_session


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
async def ready(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="finance database is unavailable",
        ) from exc

    return {
        "status": "ready",
        "service": "finance",
    }

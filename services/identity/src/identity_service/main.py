from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from identity_service.api.auth import router as auth_router
from identity_service.api.health import router as health_router
from identity_service.api.users import router as users_router
from identity_service.core.config import get_settings
from identity_service.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title="Enterprise Farm SaaS Identity Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.service_name,
        "status": "running",
    }

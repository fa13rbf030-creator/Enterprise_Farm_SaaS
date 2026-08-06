from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from finance_service.api.health import (
    router as health_router,
)
from finance_service.api.gl import router as gl_router
from finance_service.api.posting import router as posting_router
from finance_service.api.opening_balances import router as opening_balances_router
from finance_service.api.year_close import router as year_close_router
from finance_service.api.ar import router as ar_router
from finance_service.api.ap import router as ap_router
from finance_service.api.banking import router as banking_router
from finance_service.api.treasury import router as treasury_router
from finance_service.api.advanced_treasury import router as advanced_treasury_router
from finance_service.api.budgeting import router as budgeting_router
from finance_service.api.fixed_assets import router as fixed_assets_router
from finance_service.api.inquiry import router as inquiry_router
from finance_service.core.config import get_settings
from finance_service.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title="Enterprise Farm SaaS Finance Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(gl_router)
app.include_router(posting_router)
app.include_router(opening_balances_router)
app.include_router(year_close_router)
app.include_router(ar_router)
app.include_router(ap_router)
app.include_router(banking_router)
app.include_router(treasury_router)
app.include_router(advanced_treasury_router)
app.include_router(budgeting_router)
app.include_router(fixed_assets_router)
app.include_router(inquiry_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.service_name,
        "status": "running",
    }

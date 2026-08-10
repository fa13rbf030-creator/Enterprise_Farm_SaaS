from fastapi import FastAPI

from procurement_service.api.approvals import router as approvals_router
from procurement_service.api.health import router as health_router
from procurement_service.api.requisition_approvals import router as requisition_approvals_router
from procurement_service.api.purchase_order_approvals import router as purchase_order_approvals_router
from procurement_service.api.invoice_match_approvals import router as invoice_match_approvals_router
from procurement_service.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title="Enterprise Farm Procurement Service",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(approvals_router)
app.include_router(requisition_approvals_router)
app.include_router(purchase_order_approvals_router)
app.include_router(invoice_match_approvals_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.service_name,
        "status": "running",
    }

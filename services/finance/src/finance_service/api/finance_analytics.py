from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.api.gl import validate_payload_tenant
from finance_service.db.session import get_db_session
from finance_service.schemas.finance_analytics import (
    CFOExecutiveDashboardRead,
    FinanceAnalyticsSnapshotApprove,
    FinanceAnalyticsSnapshotCreate,
    FinanceAnalyticsSnapshotRead,
)
from finance_service.services.finance_analytics import (
    FinanceAnalyticsWorkflowError,
    approve_finance_analytics_snapshot,
    build_cfo_executive_dashboard,
    create_finance_analytics_snapshot,
)


router = APIRouter(
    prefix="/finance-analytics",
    tags=["finance-analytics"],
)


def translate_finance_analytics_error(
    exc: FinanceAnalyticsWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/snapshots",
    response_model=FinanceAnalyticsSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_finance_analytics_snapshot(
    payload: FinanceAnalyticsSnapshotCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_finance_analytics_snapshot(
            session,
            payload=payload,
        )
    except FinanceAnalyticsWorkflowError as exc:
        raise translate_finance_analytics_error(exc) from exc


@router.post(
    "/snapshots/{snapshot_id}/approve",
    response_model=FinanceAnalyticsSnapshotRead,
)
async def post_approve_finance_analytics_snapshot(
    snapshot_id: UUID,
    payload: FinanceAnalyticsSnapshotApprove,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await approve_finance_analytics_snapshot(
            session,
            snapshot_id=snapshot_id,
            payload=payload,
        )
    except FinanceAnalyticsWorkflowError as exc:
        raise translate_finance_analytics_error(exc) from exc


@router.get(
    "/cfo-dashboard",
    response_model=CFOExecutiveDashboardRead,
)
async def get_cfo_executive_dashboard(
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await build_cfo_executive_dashboard(
            session,
            tenant_id=x_tenant_id,
        )
    except FinanceAnalyticsWorkflowError as exc:
        raise translate_finance_analytics_error(exc) from exc

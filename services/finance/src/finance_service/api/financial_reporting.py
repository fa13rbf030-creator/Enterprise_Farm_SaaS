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
from finance_service.schemas.financial_reporting import (
    FinancialDisclosureDefinitionCreate,
    FinancialDisclosureDefinitionRead,
    FinancialReportDefinitionCreate,
    FinancialReportDefinitionRead,
    FinancialReportRunCreate,
    FinancialReportRunRead,
    FinancialReportSnapshotCreate,
    FinancialReportSnapshotRead,
)
from finance_service.services.financial_reporting import (
    FinancialReportingWorkflowError,
    complete_report_run,
    create_disclosure_definition,
    create_report_definition,
    create_report_run,
    create_report_snapshot,
    start_report_run,
)


router = APIRouter(
    prefix="/financial-reporting",
    tags=["financial-reporting"],
)


def translate_financial_reporting_error(
    exc: FinancialReportingWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/definitions",
    response_model=FinancialReportDefinitionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_report_definition(
    payload: FinancialReportDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_report_definition(
            session,
            payload=payload,
        )
    except FinancialReportingWorkflowError as exc:
        raise translate_financial_reporting_error(exc) from exc


@router.post(
    "/runs",
    response_model=FinancialReportRunRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_report_run(
    payload: FinancialReportRunCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_report_run(
            session,
            payload=payload,
        )
    except FinancialReportingWorkflowError as exc:
        raise translate_financial_reporting_error(exc) from exc


@router.post(
    "/runs/{run_id}/start",
    response_model=FinancialReportRunRead,
)
async def post_start_report_run(
    run_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await start_report_run(
            session,
            tenant_id=x_tenant_id,
            run_id=run_id,
        )
    except FinancialReportingWorkflowError as exc:
        raise translate_financial_reporting_error(exc) from exc


@router.post(
    "/runs/{run_id}/complete",
    response_model=FinancialReportRunRead,
)
async def post_complete_report_run(
    run_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await complete_report_run(
            session,
            tenant_id=x_tenant_id,
            run_id=run_id,
        )
    except FinancialReportingWorkflowError as exc:
        raise translate_financial_reporting_error(exc) from exc


@router.post(
    "/snapshots",
    response_model=FinancialReportSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_report_snapshot(
    payload: FinancialReportSnapshotCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_report_snapshot(
            session,
            payload=payload,
        )
    except FinancialReportingWorkflowError as exc:
        raise translate_financial_reporting_error(exc) from exc


@router.post(
    "/disclosures",
    response_model=FinancialDisclosureDefinitionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_disclosure_definition(
    payload: FinancialDisclosureDefinitionCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_disclosure_definition(
            session,
            payload=payload,
        )
    except FinancialReportingWorkflowError as exc:
        raise translate_financial_reporting_error(exc) from exc

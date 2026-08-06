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
from finance_service.schemas.closing import (
    FiscalYearClosePreview,
    FiscalYearCloseRead,
    FiscalYearCloseRequest,
)
from finance_service.services.year_close import (
    FiscalYearCloseWorkflowError,
    close_fiscal_year,
    preview_fiscal_year_close,
)


router = APIRouter(
    prefix="/gl/fiscal-years",
    tags=["fiscal-year-close"],
)


@router.get(
    "/{fiscal_year_id}/close-preview",
    response_model=FiscalYearClosePreview,
)
async def get_fiscal_year_close_preview(
    fiscal_year_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> FiscalYearClosePreview:
    try:
        return await preview_fiscal_year_close(
            session,
            tenant_id=x_tenant_id,
            fiscal_year_id=fiscal_year_id,
        )
    except FiscalYearCloseWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{fiscal_year_id}/close",
    response_model=FiscalYearCloseRead,
)
async def post_fiscal_year_close(
    fiscal_year_id: UUID,
    payload: FiscalYearCloseRequest,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
) -> FiscalYearCloseRead:
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await close_fiscal_year(
            session,
            tenant_id=x_tenant_id,
            fiscal_year_id=fiscal_year_id,
            retained_earnings_account_id=(
                payload.retained_earnings_account_id
            ),
            started_by=payload.started_by,
            closing_journal_number=(
                payload.closing_journal_number
            ),
        )
    except FiscalYearCloseWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

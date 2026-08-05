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

from finance_service.db.session import get_db_session
from finance_service.repositories.gl import (
    get_journal,
    list_accounts,
    list_fiscal_periods,
    list_fiscal_years,
    list_journal_lines,
)
from finance_service.schemas.gl import (
    FiscalPeriodCreate,
    FiscalPeriodRead,
    FiscalYearCreate,
    FiscalYearRead,
    JournalDetailRead,
    JournalEntryCreate,
    LedgerAccountCreate,
    LedgerAccountRead,
)
from finance_service.services.gl import (
    DuplicateFinanceRecordError,
    GlValidationError,
    create_draft_journal,
    create_fiscal_period,
    create_fiscal_year,
    create_ledger_account,
)


router = APIRouter(
    prefix="/gl",
    tags=["general-ledger"],
)


def validate_payload_tenant(
    *,
    header_tenant_id: UUID,
    payload_tenant_id: UUID,
) -> None:
    if header_tenant_id != payload_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )


@router.post(
    "/accounts",
    response_model=LedgerAccountRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_account(
    payload: LedgerAccountCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_ledger_account(
            session,
            payload=payload,
        )
    except DuplicateFinanceRecordError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except GlValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/accounts",
    response_model=list[LedgerAccountRead],
)
async def get_accounts(
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_accounts(
        session,
        tenant_id=x_tenant_id,
    )


@router.post(
    "/fiscal-years",
    response_model=FiscalYearRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_fiscal_year(
    payload: FiscalYearCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_fiscal_year(
            session,
            payload=payload,
        )
    except DuplicateFinanceRecordError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/fiscal-years",
    response_model=list[FiscalYearRead],
)
async def get_fiscal_years(
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_fiscal_years(
        session,
        tenant_id=x_tenant_id,
    )


@router.post(
    "/fiscal-periods",
    response_model=FiscalPeriodRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_fiscal_period(
    payload: FiscalPeriodCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_fiscal_period(
            session,
            payload=payload,
        )
    except DuplicateFinanceRecordError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except GlValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/fiscal-years/{fiscal_year_id}/periods",
    response_model=list[FiscalPeriodRead],
)
async def get_periods(
    fiscal_year_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_fiscal_periods(
        session,
        tenant_id=x_tenant_id,
        fiscal_year_id=fiscal_year_id,
    )


@router.post(
    "/journals",
    response_model=JournalDetailRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_journal(
    payload: JournalEntryCreate,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        journal = await create_draft_journal(
            session,
            payload=payload,
        )
    except DuplicateFinanceRecordError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except GlValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    lines = await list_journal_lines(
        session,
        tenant_id=x_tenant_id,
        journal_id=journal.id,
    )

    return {
        **JournalDetailRead.model_validate(
            {
                **journal.__dict__,
                "lines": lines,
            }
        ).model_dump()
    }


@router.get(
    "/journals/{journal_id}",
    response_model=JournalDetailRead,
)
async def get_journal_detail(
    journal_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    journal = await get_journal(
        session,
        tenant_id=x_tenant_id,
        journal_id=journal_id,
    )

    if journal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journal not found",
        )

    lines = await list_journal_lines(
        session,
        tenant_id=x_tenant_id,
        journal_id=journal.id,
    )

    return {
        **journal.__dict__,
        "lines": lines,
    }

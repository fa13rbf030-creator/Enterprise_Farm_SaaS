from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.api.gl import validate_payload_tenant
from finance_service.core.enums import (
    ReconciliationMatchType,
)
from finance_service.db.session import get_db_session
from finance_service.repositories.banking import (
    list_bank_accounts,
    list_statement_lines,
)
from finance_service.schemas.banking import (
    BankAccountCreate,
    BankAccountRead,
    BankAdjustmentCreate,
    BankStatementCreate,
    BankStatementDetailRead,
    BankStatementLineRead,
    BankStatementRead,
    CashPositionRead,
    DailyBankBalanceRead,
    ReconciliationCompleteRequest,
    ReconciliationCreate,
    ReconciliationDetailRead,
    ReconciliationMatchCreate,
    ReconciliationRead,
)
from finance_service.services.banking import (
    BankingWorkflowError,
    build_cash_position,
    build_daily_bank_balance,
    complete_reconciliation,
    create_bank_account,
    create_reconciliation,
    get_bank_statement_detail,
    get_reconciliation_detail,
    import_bank_statement,
    match_statement_line,
    post_bank_adjustment,
)


router = APIRouter(
    prefix="/banking",
    tags=["banking-reconciliation"],
)


def translate_banking_error(
    exc: BankingWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(exc),
    )


@router.post(
    "/accounts",
    response_model=BankAccountRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_bank_account(
    payload: BankAccountCreate,
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
        return await create_bank_account(
            session,
            payload=payload,
        )
    except BankingWorkflowError as exc:
        raise translate_banking_error(exc) from exc


@router.get(
    "/accounts",
    response_model=list[BankAccountRead],
)
async def get_bank_accounts(
    currency_code: str | None = None,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_bank_accounts(
        session,
        tenant_id=x_tenant_id,
        currency_code=currency_code,
    )


@router.post(
    "/statements",
    response_model=BankStatementRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_bank_statement(
    payload: BankStatementCreate,
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
        return await import_bank_statement(
            session,
            payload=payload,
        )
    except BankingWorkflowError as exc:
        raise translate_banking_error(exc) from exc


@router.get(
    "/statements/{statement_id}",
    response_model=BankStatementDetailRead,
)
async def get_statement_detail(
    statement_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await get_bank_statement_detail(
            session,
            tenant_id=x_tenant_id,
            statement_id=statement_id,
        )
    except BankingWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/statements/{statement_id}/unmatched-lines",
    response_model=list[BankStatementLineRead],
)
async def get_unmatched_statement_lines(
    statement_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_statement_lines(
        session,
        tenant_id=x_tenant_id,
        statement_id=statement_id,
        unreconciled_only=True,
    )


@router.post(
    "/reconciliations",
    response_model=ReconciliationRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_reconciliation_create(
    payload: ReconciliationCreate,
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
        return await create_reconciliation(
            session,
            payload=payload,
        )
    except BankingWorkflowError as exc:
        raise translate_banking_error(exc) from exc


@router.get(
    "/reconciliations/{reconciliation_id}",
    response_model=ReconciliationDetailRead,
)
async def get_reconciliation_endpoint(
    reconciliation_id: UUID,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await get_reconciliation_detail(
            session,
            tenant_id=x_tenant_id,
            reconciliation_id=reconciliation_id,
        )
    except BankingWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/reconciliations/{reconciliation_id}/matches",
    response_model=ReconciliationRead,
)
async def post_reconciliation_match(
    reconciliation_id: UUID,
    payload: ReconciliationMatchCreate,
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
        return await match_statement_line(
            session,
            reconciliation_id=reconciliation_id,
            payload=payload,
        )
    except BankingWorkflowError as exc:
        raise translate_banking_error(exc) from exc


@router.post(
    "/reconciliations/{reconciliation_id}/lines/"
    "{statement_line_id}/bank-charge",
    response_model=ReconciliationRead,
)
async def post_bank_charge(
    reconciliation_id: UUID,
    statement_line_id: UUID,
    payload: BankAdjustmentCreate,
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
        return await post_bank_adjustment(
            session,
            reconciliation_id=reconciliation_id,
            statement_line_id=statement_line_id,
            payload=payload,
            match_type=(
                ReconciliationMatchType.BANK_CHARGE
            ),
        )
    except BankingWorkflowError as exc:
        raise translate_banking_error(exc) from exc


@router.post(
    "/reconciliations/{reconciliation_id}/lines/"
    "{statement_line_id}/bank-interest",
    response_model=ReconciliationRead,
)
async def post_bank_interest(
    reconciliation_id: UUID,
    statement_line_id: UUID,
    payload: BankAdjustmentCreate,
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
        return await post_bank_adjustment(
            session,
            reconciliation_id=reconciliation_id,
            statement_line_id=statement_line_id,
            payload=payload,
            match_type=(
                ReconciliationMatchType.BANK_INTEREST
            ),
        )
    except BankingWorkflowError as exc:
        raise translate_banking_error(exc) from exc


@router.post(
    "/reconciliations/{reconciliation_id}/complete",
    response_model=ReconciliationRead,
)
async def post_reconciliation_complete(
    reconciliation_id: UUID,
    payload: ReconciliationCompleteRequest,
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
        return await complete_reconciliation(
            session,
            tenant_id=x_tenant_id,
            reconciliation_id=reconciliation_id,
            completed_by=payload.completed_by,
        )
    except BankingWorkflowError as exc:
        raise translate_banking_error(exc) from exc


@router.get(
    "/cash-position",
    response_model=CashPositionRead,
)
async def get_cash_position(
    currency_code: str = Query(
        default="PKR",
        min_length=3,
        max_length=3,
    ),
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    return await build_cash_position(
        session,
        tenant_id=x_tenant_id,
        currency_code=currency_code,
    )


@router.get(
    "/accounts/{bank_account_id}/daily-balance",
    response_model=DailyBankBalanceRead,
)
async def get_daily_bank_balance(
    bank_account_id: UUID,
    as_of_date: date,
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await build_daily_bank_balance(
            session,
            tenant_id=x_tenant_id,
            bank_account_id=bank_account_id,
            as_of_date=as_of_date,
        )
    except BankingWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

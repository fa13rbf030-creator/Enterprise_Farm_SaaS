from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.api.gl import validate_payload_tenant
from finance_service.db.session import get_db_session
from finance_service.models.advanced_treasury import (
    TreasuryHedgeContract,
)
from finance_service.schemas.advanced_treasury import (
    AdvancedTreasuryDashboardRead,
    CashPoolActivateRequest,
    CashPoolCreate,
    CashPoolDetailRead,
    CashPoolRead,
    CashPoolSweepRead,
    DebtInstrumentCreate,
    DebtInstrumentRead,
    FxExposureCreate,
    FxExposureRead,
    HedgeApprovalRequest,
    HedgeContractCreate,
    HedgeContractRead,
    IntercompanyTransferCreate,
    IntercompanyTransferRead,
    InvestmentCreate,
    InvestmentRead,
    StressTestCreate,
    StressTestRead,
    TradeFinanceCreate,
    TradeFinanceRead,
    TransferApprovalRequest,
)
from finance_service.services.advanced_treasury import (
    AdvancedTreasuryWorkflowError,
    activate_cash_pool,
    approve_hedge_contract,
    approve_intercompany_transfer,
    build_advanced_treasury_dashboard,
    calculate_cash_pool_sweep,
    create_cash_pool,
    create_debt_instrument,
    create_hedge_contract,
    create_intercompany_transfer,
    create_investment,
    create_trade_finance_instrument,
    get_cash_pool_detail,
    register_fx_exposure,
    run_stress_test,
)


router = APIRouter(
    prefix="/advanced-treasury",
    tags=["advanced-treasury"],
)


def translate_advanced_treasury_error(
    exc: AdvancedTreasuryWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/cash-pools",
    response_model=CashPoolRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_cash_pool(
    payload: CashPoolCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_cash_pool(
            session,
            payload=payload,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise translate_advanced_treasury_error(exc) from exc


@router.get(
    "/cash-pools/{pool_id}",
    response_model=CashPoolDetailRead,
)
async def get_cash_pool(
    pool_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await get_cash_pool_detail(
            session,
            tenant_id=x_tenant_id,
            pool_id=pool_id,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/cash-pools/{pool_id}/activate",
    response_model=CashPoolRead,
)
async def post_activate_cash_pool(
    pool_id: UUID,
    payload: CashPoolActivateRequest,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await activate_cash_pool(
            session,
            tenant_id=x_tenant_id,
            pool_id=pool_id,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise translate_advanced_treasury_error(exc) from exc


@router.get(
    "/cash-pools/{pool_id}/sweep-preview",
    response_model=CashPoolSweepRead,
)
async def get_cash_pool_sweep_preview(
    pool_id: UUID,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await calculate_cash_pool_sweep(
            session,
            tenant_id=x_tenant_id,
            pool_id=pool_id,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise translate_advanced_treasury_error(exc) from exc


@router.post(
    "/intercompany-transfers",
    response_model=IntercompanyTransferRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_intercompany_transfer(
    payload: IntercompanyTransferCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_intercompany_transfer(
            session,
            payload=payload,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise translate_advanced_treasury_error(exc) from exc


@router.post(
    "/intercompany-transfers/{transfer_id}/approve",
    response_model=IntercompanyTransferRead,
)
async def post_intercompany_transfer_approval(
    transfer_id: UUID,
    payload: TransferApprovalRequest,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await approve_intercompany_transfer(
            session,
            tenant_id=x_tenant_id,
            transfer_id=transfer_id,
            approved_by=payload.approved_by,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise translate_advanced_treasury_error(exc) from exc


@router.post(
    "/fx-exposures",
    response_model=FxExposureRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_fx_exposure(
    payload: FxExposureCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await register_fx_exposure(
            session,
            payload=payload,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise translate_advanced_treasury_error(exc) from exc


@router.post(
    "/hedges",
    response_model=HedgeContractRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_hedge_contract(
    payload: HedgeContractCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_hedge_contract(
            session,
            payload=payload,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise translate_advanced_treasury_error(exc) from exc


@router.post(
    "/hedges/{contract_id}/approve",
    response_model=HedgeContractRead,
)
async def post_hedge_approval(
    contract_id: UUID,
    payload: HedgeApprovalRequest,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    contract = await session.scalar(
        select(TreasuryHedgeContract).where(
            TreasuryHedgeContract.id == contract_id,
            TreasuryHedgeContract.tenant_id == x_tenant_id,
        )
    )

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hedge contract not found",
        )

    try:
        return await approve_hedge_contract(
            session,
            contract=contract,
            approved_by=payload.approved_by,
        )
    except AdvancedTreasuryWorkflowError as exc:
        raise translate_advanced_treasury_error(exc) from exc


@router.post(
    "/debt-instruments",
    response_model=DebtInstrumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_debt_instrument(
    payload: DebtInstrumentCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    return await create_debt_instrument(
        session,
        payload=payload,
    )


@router.post(
    "/trade-finance",
    response_model=TradeFinanceRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_trade_finance(
    payload: TradeFinanceCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    return await create_trade_finance_instrument(
        session,
        payload=payload,
    )


@router.post(
    "/investments",
    response_model=InvestmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_investment(
    payload: InvestmentCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    return await create_investment(
        session,
        payload=payload,
    )


@router.post(
    "/stress-tests",
    response_model=StressTestRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_stress_test(
    payload: StressTestCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    return await run_stress_test(
        session,
        payload=payload,
    )


@router.get(
    "/dashboard",
    response_model=AdvancedTreasuryDashboardRead,
)
async def get_advanced_treasury_dashboard(
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    return await build_advanced_treasury_dashboard(
        session,
        tenant_id=x_tenant_id,
    )

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    BankAccountStatus,
    CashPoolStatus,
    DebtStatus,
    FxExposureStatus,
    HedgeStatus,
    InvestmentStatus,
    TradeFinanceStatus,
    TreasuryTransferStatus,
)
from finance_service.models.advanced_treasury import (
    TreasuryCashPool,
    TreasuryCashPoolMember,
    TreasuryDebtInstrument,
    TreasuryFxExposure,
    TreasuryHedgeContract,
    TreasuryIntercompanyTransfer,
    TreasuryInvestment,
    TreasuryStressTest,
    TreasuryTradeFinanceInstrument,
)
from finance_service.models.banking import BankAccount
from finance_service.repositories.advanced_treasury import (
    get_cash_pool,
    get_fx_exposure,
    get_latest_stress_test,
    get_transfer,
    list_cash_pool_members,
    list_debt_instruments,
    list_fx_exposures,
    list_investments,
    list_trade_finance,
)
from finance_service.repositories.banking import get_bank_account
from finance_service.schemas.advanced_treasury import (
    AdvancedTreasuryDashboardRead,
    CashPoolCreate,
    CashPoolDetailRead,
    CashPoolSweepLineRead,
    CashPoolSweepRead,
    DebtInstrumentCreate,
    FxExposureCreate,
    HedgeContractCreate,
    IntercompanyTransferCreate,
    InvestmentCreate,
    StressTestCreate,
    TradeFinanceCreate,
)
from finance_service.services.treasury_risk_calculations import (
    calculate_expected_investment_value,
    calculate_fx_exposure,
    calculate_intercompany_transfer,
    calculate_stressed_liquidity,
    quantize_risk_money,
)


class AdvancedTreasuryWorkflowError(ValueError):
    pass


async def create_cash_pool(
    session: AsyncSession,
    *,
    payload: CashPoolCreate,
) -> TreasuryCashPool:
    header = await get_bank_account(
        session,
        tenant_id=payload.tenant_id,
        bank_account_id=payload.header_bank_account_id,
    )

    if header is None or header.status != BankAccountStatus.ACTIVE:
        raise AdvancedTreasuryWorkflowError(
            "Active header bank account not found"
        )

    if header.currency_code != payload.currency_code.upper():
        raise AdvancedTreasuryWorkflowError(
            "Cash-pool currency does not match header account"
        )

    pool = TreasuryCashPool(
        tenant_id=payload.tenant_id,
        pool_code=payload.pool_code.strip(),
        pool_name=payload.pool_name.strip(),
        pool_type=payload.pool_type,
        header_bank_account_id=payload.header_bank_account_id,
        currency_code=payload.currency_code.upper(),
        target_balance=payload.target_balance,
        created_by=payload.created_by,
    )

    session.add(pool)
    await session.flush()

    for member_payload in payload.members:
        account = await get_bank_account(
            session,
            tenant_id=payload.tenant_id,
            bank_account_id=member_payload.bank_account_id,
        )

        if account is None or account.status != BankAccountStatus.ACTIVE:
            raise AdvancedTreasuryWorkflowError(
                "Active cash-pool member account not found"
            )

        if account.currency_code != pool.currency_code:
            raise AdvancedTreasuryWorkflowError(
                "All cash-pool accounts must use one currency"
            )

        session.add(
            TreasuryCashPoolMember(
                tenant_id=payload.tenant_id,
                pool_id=pool.id,
                bank_account_id=account.id,
                minimum_balance=member_payload.minimum_balance,
                target_balance=member_payload.target_balance,
                priority=member_payload.priority,
            )
        )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AdvancedTreasuryWorkflowError(
            "Cash-pool code or member account already exists"
        ) from exc

    await session.refresh(pool)
    return pool


async def activate_cash_pool(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    pool_id: UUID,
) -> TreasuryCashPool:
    pool = await get_cash_pool(
        session,
        tenant_id=tenant_id,
        pool_id=pool_id,
        for_update=True,
    )

    if pool is None:
        raise AdvancedTreasuryWorkflowError("Cash pool not found")

    if pool.status != CashPoolStatus.DRAFT:
        raise AdvancedTreasuryWorkflowError(
            "Only draft cash pools can be activated"
        )

    pool.status = CashPoolStatus.ACTIVE
    await session.commit()
    await session.refresh(pool)

    return pool


async def get_cash_pool_detail(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    pool_id: UUID,
) -> CashPoolDetailRead:
    pool = await get_cash_pool(
        session,
        tenant_id=tenant_id,
        pool_id=pool_id,
    )

    if pool is None:
        raise AdvancedTreasuryWorkflowError("Cash pool not found")

    members = await list_cash_pool_members(
        session,
        tenant_id=tenant_id,
        pool_id=pool_id,
    )

    return CashPoolDetailRead(
        **pool.__dict__,
        members=members,
    )


async def calculate_cash_pool_sweep(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    pool_id: UUID,
) -> CashPoolSweepRead:
    pool = await get_cash_pool(
        session,
        tenant_id=tenant_id,
        pool_id=pool_id,
    )

    if pool is None or pool.status != CashPoolStatus.ACTIVE:
        raise AdvancedTreasuryWorkflowError(
            "Active cash pool not found"
        )

    header = await get_bank_account(
        session,
        tenant_id=tenant_id,
        bank_account_id=pool.header_bank_account_id,
    )

    if header is None:
        raise AdvancedTreasuryWorkflowError(
            "Header bank account not found"
        )

    members = await list_cash_pool_members(
        session,
        tenant_id=tenant_id,
        pool_id=pool.id,
    )

    lines: list[CashPoolSweepLineRead] = []
    total = Decimal("0")

    for member in members:
        account = await get_bank_account(
            session,
            tenant_id=tenant_id,
            bank_account_id=member.bank_account_id,
        )

        if account is None:
            continue

        retained = max(
            member.minimum_balance,
            member.target_balance,
        )

        sweep_amount = quantize_risk_money(
            max(account.current_balance - retained, Decimal("0"))
        )

        total += sweep_amount

        lines.append(
            CashPoolSweepLineRead(
                bank_account_id=account.id,
                current_balance=account.current_balance,
                retained_balance=retained,
                sweep_amount=sweep_amount,
            )
        )

    total = quantize_risk_money(total)

    return CashPoolSweepRead(
        pool_id=pool.id,
        currency_code=pool.currency_code,
        total_sweep_amount=total,
        header_balance_before=header.current_balance,
        header_balance_after=quantize_risk_money(
            header.current_balance + total
        ),
        lines=lines,
    )


async def create_intercompany_transfer(
    session: AsyncSession,
    *,
    payload: IntercompanyTransferCreate,
) -> TreasuryIntercompanyTransfer:
    source = await get_bank_account(
        session,
        tenant_id=payload.tenant_id,
        bank_account_id=payload.source_bank_account_id,
    )
    destination = await get_bank_account(
        session,
        tenant_id=payload.tenant_id,
        bank_account_id=payload.destination_bank_account_id,
    )

    if source is None or destination is None:
        raise AdvancedTreasuryWorkflowError(
            "Transfer bank account not found"
        )

    destination_amount = calculate_intercompany_transfer(
        source_amount=payload.amount,
        exchange_rate=payload.exchange_rate,
    )

    transfer = TreasuryIntercompanyTransfer(
        tenant_id=payload.tenant_id,
        transfer_number=payload.transfer_number.strip(),
        transfer_date=payload.transfer_date,
        source_bank_account_id=source.id,
        destination_bank_account_id=destination.id,
        amount=payload.amount,
        currency_code=payload.currency_code.upper(),
        exchange_rate=payload.exchange_rate,
        destination_amount=destination_amount,
        created_by=payload.created_by,
        notes=payload.notes.strip(),
    )

    session.add(transfer)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AdvancedTreasuryWorkflowError(
            "Transfer number already exists"
        ) from exc

    await session.refresh(transfer)
    return transfer


async def approve_intercompany_transfer(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    transfer_id: UUID,
    approved_by: UUID,
) -> TreasuryIntercompanyTransfer:
    transfer = await get_transfer(
        session,
        tenant_id=tenant_id,
        transfer_id=transfer_id,
        for_update=True,
    )

    if transfer is None:
        raise AdvancedTreasuryWorkflowError("Transfer not found")

    if transfer.created_by == approved_by:
        raise AdvancedTreasuryWorkflowError(
            "Maker cannot approve own transfer"
        )

    if transfer.status != TreasuryTransferStatus.DRAFT:
        raise AdvancedTreasuryWorkflowError(
            "Only draft transfers can be approved"
        )

    transfer.status = TreasuryTransferStatus.APPROVED
    transfer.approved_by = approved_by

    await session.commit()
    await session.refresh(transfer)

    return transfer


async def register_fx_exposure(
    session: AsyncSession,
    *,
    payload: FxExposureCreate,
) -> TreasuryFxExposure:
    base_amount, unhedged_amount = calculate_fx_exposure(
        foreign_amount=payload.foreign_amount,
        spot_rate=payload.spot_rate,
    )

    exposure = TreasuryFxExposure(
        tenant_id=payload.tenant_id,
        exposure_number=payload.exposure_number.strip(),
        exposure_type=payload.exposure_type,
        source_reference=payload.source_reference,
        exposure_date=payload.exposure_date,
        maturity_date=payload.maturity_date,
        foreign_currency=payload.foreign_currency.upper(),
        base_currency=payload.base_currency.upper(),
        foreign_amount=payload.foreign_amount,
        spot_rate=payload.spot_rate,
        base_amount=base_amount,
        hedged_amount=Decimal("0"),
        unhedged_amount=unhedged_amount,
        created_by=payload.created_by,
    )

    session.add(exposure)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AdvancedTreasuryWorkflowError(
            "FX exposure number already exists"
        ) from exc

    await session.refresh(exposure)
    return exposure


async def create_hedge_contract(
    session: AsyncSession,
    *,
    payload: HedgeContractCreate,
) -> TreasuryHedgeContract:
    exposure = await get_fx_exposure(
        session,
        tenant_id=payload.tenant_id,
        exposure_id=payload.exposure_id,
        for_update=True,
    )

    if exposure is None:
        raise AdvancedTreasuryWorkflowError(
            "FX exposure not found"
        )

    new_hedged = exposure.hedged_amount + payload.hedge_amount

    if new_hedged > exposure.foreign_amount:
        raise AdvancedTreasuryWorkflowError(
            "Hedge exceeds FX exposure"
        )

    contract = TreasuryHedgeContract(
        tenant_id=payload.tenant_id,
        exposure_id=payload.exposure_id,
        contract_number=payload.contract_number.strip(),
        instrument_type=payload.instrument_type,
        counterparty=payload.counterparty.strip(),
        trade_date=payload.trade_date,
        maturity_date=payload.maturity_date,
        hedge_amount=payload.hedge_amount,
        contracted_rate=payload.contracted_rate,
        created_by=payload.created_by,
    )

    session.add(contract)

    exposure.hedged_amount = new_hedged
    exposure.unhedged_amount = (
        exposure.foreign_amount - new_hedged
    )

    if exposure.unhedged_amount == 0:
        exposure.status = FxExposureStatus.FULLY_HEDGED
    else:
        exposure.status = FxExposureStatus.PARTIALLY_HEDGED

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise AdvancedTreasuryWorkflowError(
            "Hedge contract number already exists"
        ) from exc

    await session.refresh(contract)
    return contract


async def approve_hedge_contract(
    session: AsyncSession,
    *,
    contract: TreasuryHedgeContract,
    approved_by: UUID,
) -> TreasuryHedgeContract:
    if contract.created_by == approved_by:
        raise AdvancedTreasuryWorkflowError(
            "Maker cannot approve own hedge"
        )

    if contract.status != HedgeStatus.PROPOSED:
        raise AdvancedTreasuryWorkflowError(
            "Only proposed hedges can be approved"
        )

    contract.status = HedgeStatus.APPROVED
    contract.approved_by = approved_by

    await session.commit()
    await session.refresh(contract)

    return contract


async def create_debt_instrument(
    session: AsyncSession,
    *,
    payload: DebtInstrumentCreate,
) -> TreasuryDebtInstrument:
    instrument = TreasuryDebtInstrument(
        tenant_id=payload.tenant_id,
        instrument_number=payload.instrument_number.strip(),
        instrument_type=payload.instrument_type,
        lender_name=payload.lender_name.strip(),
        currency_code=payload.currency_code.upper(),
        principal_amount=payload.principal_amount,
        outstanding_principal=payload.principal_amount,
        annual_rate=payload.annual_rate,
        start_date=payload.start_date,
        maturity_date=payload.maturity_date,
        status=DebtStatus.ACTIVE,
        created_by=payload.created_by,
    )

    session.add(instrument)
    await session.commit()
    await session.refresh(instrument)

    return instrument


async def create_trade_finance_instrument(
    session: AsyncSession,
    *,
    payload: TradeFinanceCreate,
) -> TreasuryTradeFinanceInstrument:
    instrument = TreasuryTradeFinanceInstrument(
        tenant_id=payload.tenant_id,
        instrument_number=payload.instrument_number.strip(),
        instrument_type=payload.instrument_type,
        issuing_bank=payload.issuing_bank.strip(),
        beneficiary_name=payload.beneficiary_name.strip(),
        currency_code=payload.currency_code.upper(),
        amount=payload.amount,
        utilized_amount=Decimal("0"),
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        status=(
            TradeFinanceStatus.ISSUED
            if payload.issue_date
            else TradeFinanceStatus.REQUESTED
        ),
        created_by=payload.created_by,
    )

    session.add(instrument)
    await session.commit()
    await session.refresh(instrument)

    return instrument


async def create_investment(
    session: AsyncSession,
    *,
    payload: InvestmentCreate,
) -> TreasuryInvestment:
    term_days = (
        payload.maturity_date - payload.investment_date
    ).days

    maturity_value = calculate_expected_investment_value(
        principal=payload.principal_amount,
        annual_rate_percent=payload.expected_return_rate,
        term_days=term_days,
    )

    investment = TreasuryInvestment(
        tenant_id=payload.tenant_id,
        investment_number=payload.investment_number.strip(),
        investment_type=payload.investment_type,
        institution_name=payload.institution_name.strip(),
        currency_code=payload.currency_code.upper(),
        principal_amount=payload.principal_amount,
        expected_return_rate=payload.expected_return_rate,
        investment_date=payload.investment_date,
        maturity_date=payload.maturity_date,
        expected_maturity_value=maturity_value,
        status=InvestmentStatus.ACTIVE,
        created_by=payload.created_by,
    )

    session.add(investment)
    await session.commit()
    await session.refresh(investment)

    return investment


async def run_stress_test(
    session: AsyncSession,
    *,
    payload: StressTestCreate,
) -> TreasuryStressTest:
    stressed_liquidity, shortfall = (
        calculate_stressed_liquidity(
            opening_liquidity=payload.opening_liquidity,
            expected_inflows=payload.expected_inflows,
            expected_outflows=payload.expected_outflows,
            inflow_reduction_percent=(
                payload.inflow_reduction_percent
            ),
            outflow_increase_percent=(
                payload.outflow_increase_percent
            ),
            minimum_buffer=payload.minimum_buffer,
        )
    )

    stress_test = TreasuryStressTest(
        tenant_id=payload.tenant_id,
        test_date=payload.test_date,
        scenario_type=payload.scenario_type,
        scenario_name=payload.scenario_name.strip(),
        opening_liquidity=payload.opening_liquidity,
        inflow_reduction_percent=(
            payload.inflow_reduction_percent
        ),
        outflow_increase_percent=(
            payload.outflow_increase_percent
        ),
        fx_shock_percent=payload.fx_shock_percent,
        stressed_liquidity=stressed_liquidity,
        liquidity_shortfall=shortfall,
        created_by=payload.created_by,
    )

    session.add(stress_test)
    await session.commit()
    await session.refresh(stress_test)

    return stress_test


async def build_advanced_treasury_dashboard(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> AdvancedTreasuryDashboardRead:
    cash_pool_count = await session.scalar(
        select(TreasuryCashPool).where(
            TreasuryCashPool.tenant_id == tenant_id,
            TreasuryCashPool.status == CashPoolStatus.ACTIVE,
        ).count()
    )

    transfers = await session.execute(
        select(TreasuryIntercompanyTransfer).where(
            TreasuryIntercompanyTransfer.tenant_id == tenant_id,
            TreasuryIntercompanyTransfer.status.in_(
                [
                    TreasuryTransferStatus.DRAFT,
                    TreasuryTransferStatus.PENDING_APPROVAL,
                    TreasuryTransferStatus.APPROVED,
                ]
            ),
        )
    )

    exposures = await list_fx_exposures(
        session,
        tenant_id=tenant_id,
    )
    debts = await list_debt_instruments(
        session,
        tenant_id=tenant_id,
    )
    trade_finance = await list_trade_finance(
        session,
        tenant_id=tenant_id,
    )
    investments = await list_investments(
        session,
        tenant_id=tenant_id,
    )
    stress = await get_latest_stress_test(
        session,
        tenant_id=tenant_id,
    )

    open_exposures = [
        exposure
        for exposure in exposures
        if exposure.status
        in {
            FxExposureStatus.OPEN,
            FxExposureStatus.PARTIALLY_HEDGED,
        }
    ]

    return AdvancedTreasuryDashboardRead(
        tenant_id=tenant_id,
        active_cash_pools=int(cash_pool_count or 0),
        pending_transfers=len(transfers.scalars().all()),
        open_fx_exposures=len(open_exposures),
        total_unhedged_foreign_amount=quantize_risk_money(
            sum(
                (
                    exposure.unhedged_amount
                    for exposure in open_exposures
                ),
                Decimal("0"),
            )
        ),
        active_debt_principal=quantize_risk_money(
            sum(
                (
                    debt.outstanding_principal
                    for debt in debts
                    if debt.status == DebtStatus.ACTIVE
                ),
                Decimal("0"),
            )
        ),
        outstanding_trade_finance=quantize_risk_money(
            sum(
                (
                    instrument.amount
                    - instrument.utilized_amount
                    for instrument in trade_finance
                    if instrument.status
                    in {
                        TradeFinanceStatus.REQUESTED,
                        TradeFinanceStatus.ISSUED,
                        TradeFinanceStatus.AMENDED,
                    }
                ),
                Decimal("0"),
            )
        ),
        active_investments=quantize_risk_money(
            sum(
                (
                    investment.principal_amount
                    for investment in investments
                    if investment.status == InvestmentStatus.ACTIVE
                ),
                Decimal("0"),
            )
        ),
        latest_stress_shortfall=(
            stress.liquidity_shortfall
            if stress
            else Decimal("0")
        ),
    )

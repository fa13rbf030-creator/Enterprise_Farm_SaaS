from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    AccountType,
    FiscalPeriodStatus,
)
from finance_service.models.gl import (
    FiscalPeriod,
    FiscalYear,
    LedgerAccount,
)
from finance_service.models.posting import AccountBalance


async def get_fiscal_year_with_lock(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
) -> FiscalYear | None:
    result = await session.execute(
        select(FiscalYear)
        .where(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.tenant_id == tenant_id,
        )
        .with_for_update()
    )

    return result.scalar_one_or_none()


async def list_year_periods(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
) -> list[FiscalPeriod]:
    result = await session.execute(
        select(FiscalPeriod)
        .where(
            FiscalPeriod.tenant_id == tenant_id,
            FiscalPeriod.fiscal_year_id == fiscal_year_id,
        )
        .order_by(FiscalPeriod.period_number)
    )

    return list(result.scalars().all())


async def get_last_year_period(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
) -> FiscalPeriod | None:
    result = await session.execute(
        select(FiscalPeriod)
        .where(
            FiscalPeriod.tenant_id == tenant_id,
            FiscalPeriod.fiscal_year_id == fiscal_year_id,
        )
        .order_by(FiscalPeriod.period_number.desc())
        .limit(1)
    )

    return result.scalar_one_or_none()


async def list_temporary_account_balances(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
) -> list[tuple[LedgerAccount, AccountBalance]]:
    result = await session.execute(
        select(LedgerAccount, AccountBalance)
        .join(
            AccountBalance,
            AccountBalance.ledger_account_id
            == LedgerAccount.id,
        )
        .join(
            FiscalPeriod,
            FiscalPeriod.id
            == AccountBalance.fiscal_period_id,
        )
        .where(
            LedgerAccount.tenant_id == tenant_id,
            AccountBalance.tenant_id == tenant_id,
            FiscalPeriod.tenant_id == tenant_id,
            FiscalPeriod.fiscal_year_id == fiscal_year_id,
            LedgerAccount.account_type.in_(
                [
                    AccountType.REVENUE,
                    AccountType.EXPENSE,
                ]
            ),
        )
        .order_by(LedgerAccount.code)
    )

    return list(result.all())


async def get_retained_earnings_account(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    account_id: UUID,
) -> LedgerAccount | None:
    result = await session.execute(
        select(LedgerAccount).where(
            LedgerAccount.id == account_id,
            LedgerAccount.tenant_id == tenant_id,
            LedgerAccount.account_type == AccountType.EQUITY,
        )
    )

    return result.scalar_one_or_none()


async def count_open_periods(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
) -> int:
    periods = await list_year_periods(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
    )

    return sum(
        period.status != FiscalPeriodStatus.CLOSED
        for period in periods
    )

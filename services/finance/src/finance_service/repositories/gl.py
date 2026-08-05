from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.gl import (
    FiscalPeriod,
    FiscalYear,
    JournalEntry,
    JournalLine,
    LedgerAccount,
)


async def get_account(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    account_id: UUID,
) -> LedgerAccount | None:
    result = await session.execute(
        select(LedgerAccount).where(
            LedgerAccount.id == account_id,
            LedgerAccount.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def list_accounts(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[LedgerAccount]:
    result = await session.execute(
        select(LedgerAccount)
        .where(LedgerAccount.tenant_id == tenant_id)
        .order_by(LedgerAccount.code)
    )
    return list(result.scalars().all())


async def get_fiscal_year(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
) -> FiscalYear | None:
    result = await session.execute(
        select(FiscalYear).where(
            FiscalYear.id == fiscal_year_id,
            FiscalYear.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_fiscal_period(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_period_id: UUID,
) -> FiscalPeriod | None:
    result = await session.execute(
        select(FiscalPeriod).where(
            FiscalPeriod.id == fiscal_period_id,
            FiscalPeriod.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def list_fiscal_years(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[FiscalYear]:
    result = await session.execute(
        select(FiscalYear)
        .where(FiscalYear.tenant_id == tenant_id)
        .order_by(FiscalYear.starts_on.desc())
    )
    return list(result.scalars().all())


async def list_fiscal_periods(
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


async def get_journal(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    journal_id: UUID,
) -> JournalEntry | None:
    result = await session.execute(
        select(JournalEntry).where(
            JournalEntry.id == journal_id,
            JournalEntry.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def list_journal_lines(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    journal_id: UUID,
) -> list[JournalLine]:
    result = await session.execute(
        select(JournalLine)
        .where(
            JournalLine.tenant_id == tenant_id,
            JournalLine.journal_entry_id == journal_id,
        )
        .order_by(JournalLine.line_number)
    )
    return list(result.scalars().all())

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def get_cash_pool(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    pool_id: UUID,
    for_update: bool = False,
) -> TreasuryCashPool | None:
    query = select(TreasuryCashPool).where(
        TreasuryCashPool.id == pool_id,
        TreasuryCashPool.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_cash_pool_members(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    pool_id: UUID,
) -> list[TreasuryCashPoolMember]:
    result = await session.execute(
        select(TreasuryCashPoolMember)
        .where(
            TreasuryCashPoolMember.tenant_id == tenant_id,
            TreasuryCashPoolMember.pool_id == pool_id,
        )
        .order_by(TreasuryCashPoolMember.priority)
    )

    return list(result.scalars().all())


async def get_transfer(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    transfer_id: UUID,
    for_update: bool = False,
) -> TreasuryIntercompanyTransfer | None:
    query = select(TreasuryIntercompanyTransfer).where(
        TreasuryIntercompanyTransfer.id == transfer_id,
        TreasuryIntercompanyTransfer.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_fx_exposure(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    exposure_id: UUID,
    for_update: bool = False,
) -> TreasuryFxExposure | None:
    query = select(TreasuryFxExposure).where(
        TreasuryFxExposure.id == exposure_id,
        TreasuryFxExposure.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_fx_exposures(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[TreasuryFxExposure]:
    result = await session.execute(
        select(TreasuryFxExposure).where(
            TreasuryFxExposure.tenant_id == tenant_id
        )
    )

    return list(result.scalars().all())


async def list_debt_instruments(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[TreasuryDebtInstrument]:
    result = await session.execute(
        select(TreasuryDebtInstrument).where(
            TreasuryDebtInstrument.tenant_id == tenant_id
        )
    )

    return list(result.scalars().all())


async def list_trade_finance(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[TreasuryTradeFinanceInstrument]:
    result = await session.execute(
        select(TreasuryTradeFinanceInstrument).where(
            TreasuryTradeFinanceInstrument.tenant_id == tenant_id
        )
    )

    return list(result.scalars().all())


async def list_investments(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[TreasuryInvestment]:
    result = await session.execute(
        select(TreasuryInvestment).where(
            TreasuryInvestment.tenant_id == tenant_id
        )
    )

    return list(result.scalars().all())


async def get_latest_stress_test(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> TreasuryStressTest | None:
    result = await session.execute(
        select(TreasuryStressTest)
        .where(TreasuryStressTest.tenant_id == tenant_id)
        .order_by(
            TreasuryStressTest.test_date.desc(),
            TreasuryStressTest.created_at.desc(),
        )
        .limit(1)
    )

    return result.scalar_one_or_none()

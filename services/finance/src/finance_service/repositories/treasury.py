from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.treasury import (
    LiquidityForecast,
    TreasuryBatchApproval,
    TreasuryPaymentBatch,
    TreasuryPaymentItem,
)


async def get_treasury_batch(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
    for_update: bool = False,
) -> TreasuryPaymentBatch | None:
    query = select(TreasuryPaymentBatch).where(
        TreasuryPaymentBatch.id == batch_id,
        TreasuryPaymentBatch.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_treasury_batches(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[TreasuryPaymentBatch]:
    result = await session.execute(
        select(TreasuryPaymentBatch)
        .where(TreasuryPaymentBatch.tenant_id == tenant_id)
        .order_by(
            TreasuryPaymentBatch.batch_date.desc(),
            TreasuryPaymentBatch.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def list_treasury_items(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
) -> list[TreasuryPaymentItem]:
    result = await session.execute(
        select(TreasuryPaymentItem)
        .where(
            TreasuryPaymentItem.tenant_id == tenant_id,
            TreasuryPaymentItem.batch_id == batch_id,
        )
        .order_by(TreasuryPaymentItem.line_number)
    )

    return list(result.scalars().all())


async def get_treasury_item(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    item_id: UUID,
    for_update: bool = False,
) -> TreasuryPaymentItem | None:
    query = select(TreasuryPaymentItem).where(
        TreasuryPaymentItem.id == item_id,
        TreasuryPaymentItem.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_batch_approval(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
    approver_id: UUID,
) -> TreasuryBatchApproval | None:
    result = await session.execute(
        select(TreasuryBatchApproval).where(
            TreasuryBatchApproval.tenant_id == tenant_id,
            TreasuryBatchApproval.batch_id == batch_id,
            TreasuryBatchApproval.approver_id == approver_id,
        )
    )

    return result.scalar_one_or_none()


async def list_batch_approvals(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
) -> list[TreasuryBatchApproval]:
    result = await session.execute(
        select(TreasuryBatchApproval)
        .where(
            TreasuryBatchApproval.tenant_id == tenant_id,
            TreasuryBatchApproval.batch_id == batch_id,
        )
        .order_by(TreasuryBatchApproval.decided_at)
    )

    return list(result.scalars().all())


async def get_liquidity_forecast(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    forecast_id: UUID,
) -> LiquidityForecast | None:
    result = await session.execute(
        select(LiquidityForecast).where(
            LiquidityForecast.id == forecast_id,
            LiquidityForecast.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()


async def list_liquidity_forecasts(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    forecast_date: date | None = None,
    currency_code: str | None = None,
) -> list[LiquidityForecast]:
    query = select(LiquidityForecast).where(
        LiquidityForecast.tenant_id == tenant_id
    )

    if forecast_date is not None:
        query = query.where(
            LiquidityForecast.forecast_date == forecast_date
        )

    if currency_code is not None:
        query = query.where(
            LiquidityForecast.currency_code
            == currency_code.upper()
        )

    result = await session.execute(
        query.order_by(
            LiquidityForecast.forecast_date.desc(),
            LiquidityForecast.scenario,
        )
    )

    return list(result.scalars().all())

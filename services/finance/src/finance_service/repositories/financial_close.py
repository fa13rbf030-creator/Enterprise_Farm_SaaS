from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.financial_close import (
    FinancialCloseCycle,
    FinancialCloseTask,
    FinancialPeriodLock,
)


async def get_close_cycle(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    cycle_id: UUID,
    for_update: bool = False,
) -> FinancialCloseCycle | None:
    query = select(FinancialCloseCycle).where(
        FinancialCloseCycle.id == cycle_id,
        FinancialCloseCycle.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_close_task(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    task_id: UUID,
    for_update: bool = False,
) -> FinancialCloseTask | None:
    query = select(FinancialCloseTask).where(
        FinancialCloseTask.id == task_id,
        FinancialCloseTask.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_active_period_lock(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_period_id: UUID,
) -> FinancialPeriodLock | None:
    result = await session.execute(
        select(FinancialPeriodLock).where(
            FinancialPeriodLock.tenant_id == tenant_id,
            FinancialPeriodLock.fiscal_period_id
            == fiscal_period_id,
            FinancialPeriodLock.is_active.is_(True),
        )
    )

    return result.scalar_one_or_none()

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.closing import (
    FiscalYearCloseRun,
    OpeningBalanceBatch,
    OpeningBalanceLine,
)


async def get_opening_balance_batch(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
    for_update: bool = False,
) -> OpeningBalanceBatch | None:
    query = select(OpeningBalanceBatch).where(
        OpeningBalanceBatch.tenant_id == tenant_id,
        OpeningBalanceBatch.id == batch_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_opening_balance_lines(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    batch_id: UUID,
) -> list[OpeningBalanceLine]:
    result = await session.execute(
        select(OpeningBalanceLine)
        .where(
            OpeningBalanceLine.tenant_id == tenant_id,
            OpeningBalanceLine.batch_id == batch_id,
        )
        .order_by(OpeningBalanceLine.id)
    )

    return list(result.scalars().all())


async def get_year_close_run(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
    for_update: bool = False,
) -> FiscalYearCloseRun | None:
    query = select(FiscalYearCloseRun).where(
        FiscalYearCloseRun.tenant_id == tenant_id,
        FiscalYearCloseRun.fiscal_year_id == fiscal_year_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()

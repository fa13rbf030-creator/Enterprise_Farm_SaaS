from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.budgeting import (
    FinanceBudget,
    FinanceBudgetLine,
    FinanceBudgetVersion,
    FinanceCostCentre,
    FinanceProfitCentre,
)


async def get_budget(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    budget_id: UUID,
    for_update: bool = False,
) -> FinanceBudget | None:
    query = select(FinanceBudget).where(
        FinanceBudget.id == budget_id,
        FinanceBudget.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_latest_budget_version(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    budget_id: UUID,
) -> FinanceBudgetVersion | None:
    result = await session.execute(
        select(FinanceBudgetVersion)
        .where(
            FinanceBudgetVersion.tenant_id == tenant_id,
            FinanceBudgetVersion.budget_id == budget_id,
        )
        .order_by(FinanceBudgetVersion.version_number.desc())
        .limit(1)
    )

    return result.scalar_one_or_none()


async def list_budget_lines(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    version_id: UUID,
) -> list[FinanceBudgetLine]:
    result = await session.execute(
        select(FinanceBudgetLine)
        .where(
            FinanceBudgetLine.tenant_id == tenant_id,
            FinanceBudgetLine.version_id == version_id,
        )
        .order_by(FinanceBudgetLine.line_number)
    )

    return list(result.scalars().all())


async def get_cost_centre(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    cost_centre_id: UUID,
) -> FinanceCostCentre | None:
    result = await session.execute(
        select(FinanceCostCentre).where(
            FinanceCostCentre.id == cost_centre_id,
            FinanceCostCentre.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()


async def get_profit_centre(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    profit_centre_id: UUID,
) -> FinanceProfitCentre | None:
    result = await session.execute(
        select(FinanceProfitCentre).where(
            FinanceProfitCentre.id == profit_centre_id,
            FinanceProfitCentre.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.financial_reporting import (
    FinancialReportDefinition,
    FinancialReportLayout,
    FinancialReportRun,
)


async def get_report_definition(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    definition_id: UUID,
) -> FinancialReportDefinition | None:
    result = await session.execute(
        select(FinancialReportDefinition).where(
            FinancialReportDefinition.id == definition_id,
            FinancialReportDefinition.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()


async def get_report_layout(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    layout_id: UUID,
) -> FinancialReportLayout | None:
    result = await session.execute(
        select(FinancialReportLayout).where(
            FinancialReportLayout.id == layout_id,
            FinancialReportLayout.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()


async def get_report_run(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    run_id: UUID,
    for_update: bool = False,
) -> FinancialReportRun | None:
    query = select(FinancialReportRun).where(
        FinancialReportRun.id == run_id,
        FinancialReportRun.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()

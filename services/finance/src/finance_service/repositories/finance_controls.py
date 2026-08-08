from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.finance_controls import (
    FinanceControlDefinition,
    FinanceControlExecution,
    FinanceReconciliationRun,
)


async def get_control_definition(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    control_id: UUID,
) -> FinanceControlDefinition | None:
    result = await session.execute(
        select(FinanceControlDefinition).where(
            FinanceControlDefinition.id == control_id,
            FinanceControlDefinition.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_control_execution(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    execution_id: UUID,
) -> FinanceControlExecution | None:
    result = await session.execute(
        select(FinanceControlExecution).where(
            FinanceControlExecution.id == execution_id,
            FinanceControlExecution.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_reconciliation_run(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    reconciliation_id: UUID,
) -> FinanceReconciliationRun | None:
    result = await session.execute(
        select(FinanceReconciliationRun).where(
            FinanceReconciliationRun.id == reconciliation_id,
            FinanceReconciliationRun.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()

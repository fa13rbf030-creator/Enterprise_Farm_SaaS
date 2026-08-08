from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.finance_analytics import (
    FinanceAnalyticsSnapshot,
    FinanceAnalyticsSnapshotStatus,
)


async def get_finance_analytics_snapshot(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    snapshot_id: UUID,
    for_update: bool = False,
) -> FinanceAnalyticsSnapshot | None:
    query = select(FinanceAnalyticsSnapshot).where(
        FinanceAnalyticsSnapshot.id == snapshot_id,
        FinanceAnalyticsSnapshot.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_latest_finance_analytics_snapshot(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    approved_only: bool = False,
) -> FinanceAnalyticsSnapshot | None:
    query = (
        select(FinanceAnalyticsSnapshot)
        .where(
            FinanceAnalyticsSnapshot.tenant_id == tenant_id
        )
        .order_by(
            FinanceAnalyticsSnapshot.period_end.desc(),
            FinanceAnalyticsSnapshot.created_at.desc(),
        )
        .limit(1)
    )

    if approved_only:
        query = query.where(
            FinanceAnalyticsSnapshot.status
            == FinanceAnalyticsSnapshotStatus.APPROVED
        )

    result = await session.execute(query)
    return result.scalar_one_or_none()

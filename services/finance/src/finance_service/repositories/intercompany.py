from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.intercompany import (
    ConsolidationGroup,
    ConsolidationPeriod,
    IntercompanyAccountMapping,
    IntercompanyOrganization,
    IntercompanyTransaction,
)


async def get_intercompany_organization(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    organization_id: UUID,
) -> IntercompanyOrganization | None:
    result = await session.execute(
        select(IntercompanyOrganization).where(
            IntercompanyOrganization.id == organization_id,
            IntercompanyOrganization.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()


async def get_consolidation_group(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    group_id: UUID,
) -> ConsolidationGroup | None:
    result = await session.execute(
        select(ConsolidationGroup).where(
            ConsolidationGroup.id == group_id,
            ConsolidationGroup.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()


async def get_consolidation_period(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    period_id: UUID,
    for_update: bool = False,
) -> ConsolidationPeriod | None:
    query = select(ConsolidationPeriod).where(
        ConsolidationPeriod.id == period_id,
        ConsolidationPeriod.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_intercompany_transaction(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    transaction_id: UUID,
    for_update: bool = False,
) -> IntercompanyTransaction | None:
    query = select(IntercompanyTransaction).where(
        IntercompanyTransaction.id == transaction_id,
        IntercompanyTransaction.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_account_mapping(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    source_organization_id: UUID,
    destination_organization_id: UUID,
) -> IntercompanyAccountMapping | None:
    result = await session.execute(
        select(IntercompanyAccountMapping).where(
            IntercompanyAccountMapping.tenant_id == tenant_id,
            IntercompanyAccountMapping.source_organization_id
            == source_organization_id,
            IntercompanyAccountMapping.destination_organization_id
            == destination_organization_id,
            IntercompanyAccountMapping.is_active.is_(True),
        )
    )

    return result.scalar_one_or_none()

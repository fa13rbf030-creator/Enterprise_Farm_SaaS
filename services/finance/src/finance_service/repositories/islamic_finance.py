from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.islamic_finance import (
    NisabReference,
    ShariahRuleSet,
    UshrAssessment,
    ZakatAssessment,
)


async def get_shariah_rule_set(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    rule_set_id: UUID,
    for_update: bool = False,
) -> ShariahRuleSet | None:
    query = select(ShariahRuleSet).where(
        ShariahRuleSet.id == rule_set_id,
        ShariahRuleSet.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_nisab_reference(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    nisab_reference_id: UUID,
) -> NisabReference | None:
    result = await session.execute(
        select(NisabReference).where(
            NisabReference.id == nisab_reference_id,
            NisabReference.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_zakat_assessment(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    assessment_id: UUID,
) -> ZakatAssessment | None:
    result = await session.execute(
        select(ZakatAssessment).where(
            ZakatAssessment.id == assessment_id,
            ZakatAssessment.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_ushr_assessment(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    assessment_id: UUID,
) -> UshrAssessment | None:
    result = await session.execute(
        select(UshrAssessment).where(
            UshrAssessment.id == assessment_id,
            UshrAssessment.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()

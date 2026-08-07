from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.tax_compliance import (
    TaxCode,
    TaxJurisdiction,
    TaxPeriod,
    TaxRegistration,
    TaxReturn,
)


async def get_tax_jurisdiction(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    jurisdiction_id: UUID,
) -> TaxJurisdiction | None:
    result = await session.execute(
        select(TaxJurisdiction).where(
            TaxJurisdiction.id == jurisdiction_id,
            TaxJurisdiction.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_tax_registration(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    registration_id: UUID,
) -> TaxRegistration | None:
    result = await session.execute(
        select(TaxRegistration).where(
            TaxRegistration.id == registration_id,
            TaxRegistration.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_tax_code(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    tax_code_id: UUID,
) -> TaxCode | None:
    result = await session.execute(
        select(TaxCode).where(
            TaxCode.id == tax_code_id,
            TaxCode.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_tax_period(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    tax_period_id: UUID,
) -> TaxPeriod | None:
    result = await session.execute(
        select(TaxPeriod).where(
            TaxPeriod.id == tax_period_id,
            TaxPeriod.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_tax_return(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    tax_return_id: UUID,
) -> TaxReturn | None:
    result = await session.execute(
        select(TaxReturn).where(
            TaxReturn.id == tax_return_id,
            TaxReturn.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()

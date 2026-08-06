from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.fixed_assets import (
    FixedAsset,
    FixedAssetCategory,
    FixedAssetLocation,
)


async def get_asset_category(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    category_id: UUID,
) -> FixedAssetCategory | None:
    result = await session.execute(
        select(FixedAssetCategory).where(
            FixedAssetCategory.id == category_id,
            FixedAssetCategory.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()


async def get_asset_location(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    location_id: UUID,
) -> FixedAssetLocation | None:
    result = await session.execute(
        select(FixedAssetLocation).where(
            FixedAssetLocation.id == location_id,
            FixedAssetLocation.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()


async def get_fixed_asset(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    asset_id: UUID,
    for_update: bool = False,
) -> FixedAsset | None:
    query = select(FixedAsset).where(
        FixedAsset.id == asset_id,
        FixedAsset.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()

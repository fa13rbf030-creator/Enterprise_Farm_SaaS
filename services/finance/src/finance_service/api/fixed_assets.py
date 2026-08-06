from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.api.gl import validate_payload_tenant
from finance_service.db.session import get_db_session
from finance_service.schemas.fixed_assets import (
    AssetCategoryCreate,
    AssetCategoryRead,
    AssetDisposalCreate,
    AssetDisposalRead,
    AssetImpairmentCreate,
    AssetLocationCreate,
    AssetLocationRead,
    AssetRevaluationCreate,
    AssetTransferCreate,
    DepreciationBookCreate,
    DepreciationBookRead,
    FixedAssetCreate,
    FixedAssetRead,
)
from finance_service.services.fixed_assets import (
    FixedAssetWorkflowError,
    create_asset_category,
    create_asset_location,
    create_depreciation_book,
    create_fixed_asset,
    dispose_asset,
    impair_asset,
    revalue_asset,
    transfer_asset,
)


router = APIRouter(
    prefix="/fixed-assets",
    tags=["fixed-assets"],
)


def translate_fixed_asset_error(
    exc: FixedAssetWorkflowError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


@router.post(
    "/categories",
    response_model=AssetCategoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_asset_category(
    payload: AssetCategoryCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_asset_category(
            session,
            payload=payload,
        )
    except FixedAssetWorkflowError as exc:
        raise translate_fixed_asset_error(exc) from exc


@router.post(
    "/locations",
    response_model=AssetLocationRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_asset_location(
    payload: AssetLocationCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_asset_location(
            session,
            payload=payload,
        )
    except FixedAssetWorkflowError as exc:
        raise translate_fixed_asset_error(exc) from exc


@router.post(
    "/assets",
    response_model=FixedAssetRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_fixed_asset(
    payload: FixedAssetCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_fixed_asset(
            session,
            payload=payload,
        )
    except FixedAssetWorkflowError as exc:
        raise translate_fixed_asset_error(exc) from exc


@router.post(
    "/assets/{asset_id}/depreciation-books",
    response_model=DepreciationBookRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_depreciation_book(
    asset_id: UUID,
    payload: DepreciationBookCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await create_depreciation_book(
            session,
            asset_id=asset_id,
            payload=payload,
        )
    except FixedAssetWorkflowError as exc:
        raise translate_fixed_asset_error(exc) from exc


@router.post(
    "/assets/{asset_id}/transfer",
    response_model=FixedAssetRead,
)
async def post_asset_transfer(
    asset_id: UUID,
    payload: AssetTransferCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await transfer_asset(
            session,
            asset_id=asset_id,
            payload=payload,
        )
    except FixedAssetWorkflowError as exc:
        raise translate_fixed_asset_error(exc) from exc


@router.post(
    "/assets/{asset_id}/revalue",
    response_model=FixedAssetRead,
)
async def post_asset_revaluation(
    asset_id: UUID,
    payload: AssetRevaluationCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await revalue_asset(
            session,
            asset_id=asset_id,
            payload=payload,
        )
    except FixedAssetWorkflowError as exc:
        raise translate_fixed_asset_error(exc) from exc


@router.post(
    "/assets/{asset_id}/impair",
    response_model=FixedAssetRead,
)
async def post_asset_impairment(
    asset_id: UUID,
    payload: AssetImpairmentCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await impair_asset(
            session,
            asset_id=asset_id,
            payload=payload,
        )
    except FixedAssetWorkflowError as exc:
        raise translate_fixed_asset_error(exc) from exc


@router.post(
    "/assets/{asset_id}/dispose",
    response_model=AssetDisposalRead,
)
async def post_asset_disposal(
    asset_id: UUID,
    payload: AssetDisposalCreate,
    x_tenant_id: UUID = Header(..., alias="X-Tenant-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    validate_payload_tenant(
        header_tenant_id=x_tenant_id,
        payload_tenant_id=payload.tenant_id,
    )

    try:
        return await dispose_asset(
            session,
            asset_id=asset_id,
            payload=payload,
        )
    except FixedAssetWorkflowError as exc:
        raise translate_fixed_asset_error(exc) from exc

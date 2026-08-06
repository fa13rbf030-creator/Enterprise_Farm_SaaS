from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    AssetStatus,
    AssetTransactionType,
)
from finance_service.models.fixed_assets import (
    FixedAsset,
    FixedAssetCategory,
    FixedAssetDepreciationBook,
    FixedAssetDisposal,
    FixedAssetLocation,
    FixedAssetTransaction,
)
from finance_service.repositories.fixed_assets import (
    get_asset_category,
    get_asset_location,
    get_fixed_asset,
)
from finance_service.schemas.fixed_assets import (
    AssetCategoryCreate,
    AssetDisposalCreate,
    AssetImpairmentCreate,
    AssetLocationCreate,
    AssetRevaluationCreate,
    AssetTransferCreate,
    DepreciationBookCreate,
    FixedAssetCreate,
)
from finance_service.services.fixed_asset_calculations import (
    calculate_disposal_gain_loss,
    calculate_revaluation_surplus,
)


class FixedAssetWorkflowError(ValueError):
    pass


async def create_asset_category(
    session: AsyncSession,
    *,
    payload: AssetCategoryCreate,
) -> FixedAssetCategory:
    if payload.parent_id is not None:
        parent = await get_asset_category(
            session,
            tenant_id=payload.tenant_id,
            category_id=payload.parent_id,
        )

        if parent is None:
            raise FixedAssetWorkflowError(
                "Parent asset category not found"
            )

    category = FixedAssetCategory(
        tenant_id=payload.tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        parent_id=payload.parent_id,
        default_useful_life_months=(
            payload.default_useful_life_months
        ),
        default_depreciation_method=(
            payload.default_depreciation_method
        ),
        asset_account_id=payload.asset_account_id,
        accumulated_depreciation_account_id=(
            payload.accumulated_depreciation_account_id
        ),
        depreciation_expense_account_id=(
            payload.depreciation_expense_account_id
        ),
        disposal_gain_account_id=(
            payload.disposal_gain_account_id
        ),
        disposal_loss_account_id=(
            payload.disposal_loss_account_id
        ),
    )

    session.add(category)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FixedAssetWorkflowError(
            "Asset-category code already exists"
        ) from exc

    await session.refresh(category)
    return category


async def create_asset_location(
    session: AsyncSession,
    *,
    payload: AssetLocationCreate,
) -> FixedAssetLocation:
    if payload.parent_id is not None:
        parent = await get_asset_location(
            session,
            tenant_id=payload.tenant_id,
            location_id=payload.parent_id,
        )

        if parent is None:
            raise FixedAssetWorkflowError(
                "Parent asset location not found"
            )

    location = FixedAssetLocation(
        tenant_id=payload.tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        farm_id=payload.farm_id,
        branch_id=payload.branch_id,
        parent_id=payload.parent_id,
        address=payload.address.strip(),
    )

    session.add(location)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FixedAssetWorkflowError(
            "Asset-location code already exists"
        ) from exc

    await session.refresh(location)
    return location


async def create_fixed_asset(
    session: AsyncSession,
    *,
    payload: FixedAssetCreate,
) -> FixedAsset:
    category = await get_asset_category(
        session,
        tenant_id=payload.tenant_id,
        category_id=payload.category_id,
    )

    if category is None:
        raise FixedAssetWorkflowError(
            "Asset category not found"
        )

    if payload.location_id is not None:
        location = await get_asset_location(
            session,
            tenant_id=payload.tenant_id,
            location_id=payload.location_id,
        )

        if location is None:
            raise FixedAssetWorkflowError(
                "Asset location not found"
            )

    status = (
        AssetStatus.ACTIVE
        if payload.capitalization_date is not None
        else AssetStatus.DRAFT
    )

    asset = FixedAsset(
        tenant_id=payload.tenant_id,
        asset_number=payload.asset_number.strip(),
        name=payload.name.strip(),
        description=payload.description.strip(),
        category_id=payload.category_id,
        location_id=payload.location_id,
        custodian_id=payload.custodian_id,
        cost_centre_id=payload.cost_centre_id,
        profit_centre_id=payload.profit_centre_id,
        acquisition_type=payload.acquisition_type,
        acquisition_date=payload.acquisition_date,
        capitalization_date=payload.capitalization_date,
        supplier_id=payload.supplier_id,
        source_document_reference=(
            payload.source_document_reference
        ),
        acquisition_cost=payload.acquisition_cost,
        residual_value=payload.residual_value,
        accumulated_depreciation=Decimal("0"),
        impairment_amount=Decimal("0"),
        revaluation_amount=Decimal("0"),
        net_book_value=payload.acquisition_cost,
        useful_life_months=payload.useful_life_months,
        depreciation_method=payload.depreciation_method,
        depreciation_start_date=(
            payload.depreciation_start_date
        ),
        estimated_total_units=payload.estimated_total_units,
        units_consumed=Decimal("0"),
        status=status,
        barcode=payload.barcode,
        qr_code=payload.qr_code,
        serial_number=payload.serial_number,
        manufacturer=payload.manufacturer,
        model_number=payload.model_number,
        cmms_asset_reference=payload.cmms_asset_reference,
        created_by=payload.created_by,
    )

    session.add(asset)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FixedAssetWorkflowError(
            "Asset number or barcode already exists"
        ) from exc

    await session.refresh(asset)
    return asset


async def create_depreciation_book(
    session: AsyncSession,
    *,
    asset_id: UUID,
    payload: DepreciationBookCreate,
) -> FixedAssetDepreciationBook:
    asset = await get_fixed_asset(
        session,
        tenant_id=payload.tenant_id,
        asset_id=asset_id,
    )

    if asset is None:
        raise FixedAssetWorkflowError(
            "Fixed asset not found"
        )

    if payload.residual_value > asset.acquisition_cost:
        raise FixedAssetWorkflowError(
            "Book residual value exceeds asset cost"
        )

    book = FixedAssetDepreciationBook(
        tenant_id=payload.tenant_id,
        asset_id=asset.id,
        book_type=payload.book_type,
        depreciation_method=payload.depreciation_method,
        useful_life_months=payload.useful_life_months,
        annual_rate_percent=payload.annual_rate_percent,
        residual_value=payload.residual_value,
        accumulated_depreciation=Decimal("0"),
        net_book_value=asset.acquisition_cost,
    )

    session.add(book)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FixedAssetWorkflowError(
            "Depreciation book already exists"
        ) from exc

    await session.refresh(book)
    return book


async def transfer_asset(
    session: AsyncSession,
    *,
    asset_id: UUID,
    payload: AssetTransferCreate,
) -> FixedAsset:
    asset = await get_fixed_asset(
        session,
        tenant_id=payload.tenant_id,
        asset_id=asset_id,
        for_update=True,
    )

    if asset is None:
        raise FixedAssetWorkflowError(
            "Fixed asset not found"
        )

    destination = await get_asset_location(
        session,
        tenant_id=payload.tenant_id,
        location_id=payload.to_location_id,
    )

    if destination is None:
        raise FixedAssetWorkflowError(
            "Destination location not found"
        )

    transaction = FixedAssetTransaction(
        tenant_id=payload.tenant_id,
        asset_id=asset.id,
        transaction_number=payload.transaction_number.strip(),
        transaction_type=AssetTransactionType.TRANSFER,
        transaction_date=payload.transaction_date,
        amount=Decimal("0"),
        from_location_id=asset.location_id,
        to_location_id=payload.to_location_id,
        notes=payload.notes.strip(),
        created_by=payload.created_by,
    )

    asset.location_id = payload.to_location_id
    session.add(transaction)

    await session.commit()
    await session.refresh(asset)

    return asset


async def revalue_asset(
    session: AsyncSession,
    *,
    asset_id: UUID,
    payload: AssetRevaluationCreate,
) -> FixedAsset:
    asset = await get_fixed_asset(
        session,
        tenant_id=payload.tenant_id,
        asset_id=asset_id,
        for_update=True,
    )

    if asset is None:
        raise FixedAssetWorkflowError(
            "Fixed asset not found"
        )

    surplus = calculate_revaluation_surplus(
        current_net_book_value=asset.net_book_value,
        revalued_amount=payload.revalued_amount,
    )

    transaction = FixedAssetTransaction(
        tenant_id=payload.tenant_id,
        asset_id=asset.id,
        transaction_number=payload.transaction_number.strip(),
        transaction_type=AssetTransactionType.REVALUATION,
        transaction_date=payload.transaction_date,
        amount=surplus,
        notes=payload.notes.strip(),
        created_by=payload.created_by,
    )

    asset.revaluation_amount += surplus
    asset.net_book_value = payload.revalued_amount

    session.add(transaction)
    await session.commit()
    await session.refresh(asset)

    return asset


async def impair_asset(
    session: AsyncSession,
    *,
    asset_id: UUID,
    payload: AssetImpairmentCreate,
) -> FixedAsset:
    asset = await get_fixed_asset(
        session,
        tenant_id=payload.tenant_id,
        asset_id=asset_id,
        for_update=True,
    )

    if asset is None:
        raise FixedAssetWorkflowError(
            "Fixed asset not found"
        )

    impairment = max(
        asset.net_book_value - payload.recoverable_amount,
        Decimal("0"),
    )

    transaction = FixedAssetTransaction(
        tenant_id=payload.tenant_id,
        asset_id=asset.id,
        transaction_number=payload.transaction_number.strip(),
        transaction_type=AssetTransactionType.IMPAIRMENT,
        transaction_date=payload.transaction_date,
        amount=impairment,
        notes=payload.notes.strip(),
        created_by=payload.created_by,
    )

    asset.impairment_amount += impairment
    asset.net_book_value -= impairment

    if impairment > 0:
        asset.status = AssetStatus.IMPAIRED

    session.add(transaction)
    await session.commit()
    await session.refresh(asset)

    return asset


async def dispose_asset(
    session: AsyncSession,
    *,
    asset_id: UUID,
    payload: AssetDisposalCreate,
) -> FixedAssetDisposal:
    asset = await get_fixed_asset(
        session,
        tenant_id=payload.tenant_id,
        asset_id=asset_id,
        for_update=True,
    )

    if asset is None:
        raise FixedAssetWorkflowError(
            "Fixed asset not found"
        )

    if asset.status == AssetStatus.DISPOSED:
        raise FixedAssetWorkflowError(
            "Asset is already disposed"
        )

    gain_loss = calculate_disposal_gain_loss(
        disposal_proceeds=payload.proceeds,
        net_book_value=asset.net_book_value,
        disposal_costs=payload.disposal_costs,
    )

    disposal = FixedAssetDisposal(
        tenant_id=payload.tenant_id,
        asset_id=asset.id,
        disposal_type=payload.disposal_type,
        disposal_date=payload.disposal_date,
        proceeds=payload.proceeds,
        disposal_costs=payload.disposal_costs,
        net_book_value=asset.net_book_value,
        gain_loss=gain_loss,
        buyer_reference=payload.buyer_reference,
        disposed_by=payload.disposed_by,
    )

    asset.status = AssetStatus.DISPOSED
    session.add(disposal)

    await session.commit()
    await session.refresh(disposal)

    return disposal

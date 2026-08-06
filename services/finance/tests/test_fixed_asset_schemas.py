from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.core.enums import (
    AssetAcquisitionType,
    DepreciationMethod,
)
from finance_service.schemas.fixed_assets import (
    FixedAssetCreate,
)


def test_asset_rejects_residual_above_cost() -> None:
    with pytest.raises(ValidationError):
        FixedAssetCreate(
            tenant_id=uuid4(),
            asset_number="FA-001",
            name="Tractor",
            category_id=uuid4(),
            acquisition_type=AssetAcquisitionType.PURCHASE,
            acquisition_date=date(2026, 8, 6),
            acquisition_cost=Decimal("100"),
            residual_value=Decimal("101"),
            useful_life_months=60,
            depreciation_method=DepreciationMethod.STRAIGHT_LINE,
            created_by=uuid4(),
        )


def test_units_method_requires_estimated_units() -> None:
    with pytest.raises(ValidationError):
        FixedAssetCreate(
            tenant_id=uuid4(),
            asset_number="FA-002",
            name="Production Machine",
            category_id=uuid4(),
            acquisition_type=AssetAcquisitionType.PURCHASE,
            acquisition_date=date(2026, 8, 6),
            acquisition_cost=Decimal("100000"),
            useful_life_months=60,
            depreciation_method=(
                DepreciationMethod.UNITS_OF_PRODUCTION
            ),
            created_by=uuid4(),
        )

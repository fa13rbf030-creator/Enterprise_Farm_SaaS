from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from finance_service.core.enums import (
    AssetAcquisitionType,
    AssetDisposalType,
    AssetStatus,
    DepreciationBookType,
    DepreciationMethod,
)


class AssetCategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    parent_id: UUID | None = None
    default_useful_life_months: int = Field(default=60, gt=0)
    default_depreciation_method: DepreciationMethod
    asset_account_id: UUID
    accumulated_depreciation_account_id: UUID
    depreciation_expense_account_id: UUID
    disposal_gain_account_id: UUID | None = None
    disposal_loss_account_id: UUID | None = None


class AssetCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    parent_id: UUID | None
    default_useful_life_months: int
    default_depreciation_method: DepreciationMethod
    asset_account_id: UUID
    accumulated_depreciation_account_id: UUID
    depreciation_expense_account_id: UUID
    disposal_gain_account_id: UUID | None
    disposal_loss_account_id: UUID | None
    is_active: bool


class AssetLocationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    farm_id: UUID | None = None
    branch_id: UUID | None = None
    parent_id: UUID | None = None
    address: str = Field(default="", max_length=2000)


class AssetLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    farm_id: UUID | None
    branch_id: UUID | None
    parent_id: UUID | None
    address: str
    is_active: bool


class FixedAssetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    asset_number: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    category_id: UUID
    location_id: UUID | None = None
    custodian_id: UUID | None = None
    cost_centre_id: UUID | None = None
    profit_centre_id: UUID | None = None
    acquisition_type: AssetAcquisitionType
    acquisition_date: date
    capitalization_date: date | None = None
    supplier_id: UUID | None = None
    source_document_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    acquisition_cost: Decimal = Field(gt=0)
    residual_value: Decimal = Field(default=Decimal("0"), ge=0)
    useful_life_months: int = Field(gt=0)
    depreciation_method: DepreciationMethod
    depreciation_start_date: date | None = None
    estimated_total_units: Decimal | None = Field(default=None, gt=0)
    barcode: str | None = Field(default=None, max_length=200)
    qr_code: str | None = Field(default=None, max_length=500)
    serial_number: str | None = Field(default=None, max_length=200)
    manufacturer: str | None = Field(default=None, max_length=200)
    model_number: str | None = Field(default=None, max_length=200)
    cmms_asset_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    created_by: UUID

    @model_validator(mode="after")
    def validate_asset(self):
        if self.residual_value > self.acquisition_cost:
            raise ValueError(
                "Residual value cannot exceed acquisition cost"
            )

        if (
            self.capitalization_date is not None
            and self.capitalization_date < self.acquisition_date
        ):
            raise ValueError(
                "Capitalization date cannot precede acquisition date"
            )

        if (
            self.depreciation_method
            == DepreciationMethod.UNITS_OF_PRODUCTION
            and self.estimated_total_units is None
        ):
            raise ValueError(
                "Units-of-production method requires estimated units"
            )

        return self


class FixedAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    asset_number: str
    name: str
    category_id: UUID
    location_id: UUID | None
    custodian_id: UUID | None
    acquisition_type: AssetAcquisitionType
    acquisition_date: date
    capitalization_date: date | None
    acquisition_cost: Decimal
    residual_value: Decimal
    accumulated_depreciation: Decimal
    impairment_amount: Decimal
    revaluation_amount: Decimal
    net_book_value: Decimal
    useful_life_months: int
    depreciation_method: DepreciationMethod
    depreciation_start_date: date | None
    estimated_total_units: Decimal | None
    units_consumed: Decimal
    status: AssetStatus
    barcode: str | None
    serial_number: str | None
    cmms_asset_reference: str | None


class DepreciationBookCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    book_type: DepreciationBookType
    depreciation_method: DepreciationMethod
    useful_life_months: int = Field(gt=0)
    annual_rate_percent: Decimal | None = Field(default=None, ge=0)
    residual_value: Decimal = Field(default=Decimal("0"), ge=0)

    @model_validator(mode="after")
    def validate_book(self):
        if (
            self.depreciation_method
            == DepreciationMethod.REDUCING_BALANCE
            and self.annual_rate_percent is None
        ):
            raise ValueError(
                "Reducing-balance book requires annual rate"
            )

        return self


class DepreciationBookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    asset_id: UUID
    book_type: DepreciationBookType
    depreciation_method: DepreciationMethod
    useful_life_months: int
    annual_rate_percent: Decimal | None
    residual_value: Decimal
    accumulated_depreciation: Decimal
    net_book_value: Decimal
    last_depreciation_date: date | None
    is_active: bool


class AssetTransferCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    transaction_number: str = Field(min_length=1, max_length=100)
    transaction_date: date
    to_location_id: UUID
    created_by: UUID
    notes: str = Field(default="", max_length=2000)


class AssetRevaluationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    transaction_number: str = Field(min_length=1, max_length=100)
    transaction_date: date
    revalued_amount: Decimal = Field(ge=0)
    created_by: UUID
    notes: str = Field(default="", max_length=2000)


class AssetImpairmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    transaction_number: str = Field(min_length=1, max_length=100)
    transaction_date: date
    recoverable_amount: Decimal = Field(ge=0)
    created_by: UUID
    notes: str = Field(default="", max_length=2000)


class AssetDisposalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    disposal_type: AssetDisposalType
    disposal_date: date
    proceeds: Decimal = Field(default=Decimal("0"), ge=0)
    disposal_costs: Decimal = Field(default=Decimal("0"), ge=0)
    buyer_reference: str | None = Field(
        default=None,
        max_length=200,
    )
    disposed_by: UUID


class AssetDisposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    asset_id: UUID
    disposal_type: AssetDisposalType
    disposal_date: date
    proceeds: Decimal
    disposal_costs: Decimal
    net_book_value: Decimal
    gain_loss: Decimal
    buyer_reference: str | None
    journal_entry_id: UUID | None
    disposed_by: UUID

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.core.enums import (
    AssetAcquisitionType,
    AssetDisposalType,
    AssetProjectStatus,
    AssetStatus,
    AssetTransactionType,
    DepreciationBookType,
    DepreciationMethod,
)
from finance_service.db.base import Base


class FixedAssetCategory(Base):
    __tablename__ = "finance_asset_categories"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_finance_asset_category_tenant_code",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_asset_categories.id"),
        nullable=True,
    )
    default_useful_life_months: Mapped[int] = mapped_column(
        nullable=False,
        default=60,
    )
    default_depreciation_method: Mapped[DepreciationMethod] = mapped_column(
        Enum(
            DepreciationMethod,
            name="finance_asset_default_depreciation_method",
        ),
        nullable=False,
        default=DepreciationMethod.STRAIGHT_LINE,
    )
    asset_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=False,
    )
    accumulated_depreciation_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=False,
    )
    depreciation_expense_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=False,
    )
    disposal_gain_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=True,
    )
    disposal_loss_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )


class FixedAssetLocation(Base):
    __tablename__ = "finance_asset_locations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_finance_asset_location_tenant_code",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    farm_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    branch_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_asset_locations.id"),
        nullable=True,
    )
    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )


class FixedAsset(Base):
    __tablename__ = "finance_fixed_assets"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "asset_number",
            name="uq_finance_fixed_asset_tenant_number",
        ),
        UniqueConstraint(
            "tenant_id",
            "barcode",
            name="uq_finance_fixed_asset_tenant_barcode",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    asset_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_asset_categories.id"),
        nullable=False,
    )
    location_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_asset_locations.id"),
        nullable=True,
    )
    custodian_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    cost_centre_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_cost_centres.id"),
        nullable=True,
    )
    profit_centre_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_profit_centres.id"),
        nullable=True,
    )
    acquisition_type: Mapped[AssetAcquisitionType] = mapped_column(
        Enum(
            AssetAcquisitionType,
            name="finance_asset_acquisition_type",
        ),
        nullable=False,
    )
    acquisition_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    capitalization_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    supplier_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    source_document_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    acquisition_cost: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    residual_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    impairment_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    revaluation_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    net_book_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    useful_life_months: Mapped[int] = mapped_column(
        nullable=False,
    )
    depreciation_method: Mapped[DepreciationMethod] = mapped_column(
        Enum(
            DepreciationMethod,
            name="finance_asset_depreciation_method",
        ),
        nullable=False,
    )
    depreciation_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    estimated_total_units: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 6),
        nullable=True,
    )
    units_consumed: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="finance_asset_status"),
        nullable=False,
        default=AssetStatus.DRAFT,
    )
    barcode: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    qr_code: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    serial_number: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    manufacturer: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    model_number: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    cmms_asset_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class FixedAssetDepreciationBook(Base):
    __tablename__ = "finance_asset_depreciation_books"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "book_type",
            name="uq_finance_asset_depreciation_book",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fixed_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    book_type: Mapped[DepreciationBookType] = mapped_column(
        Enum(
            DepreciationBookType,
            name="finance_asset_depreciation_book_type",
        ),
        nullable=False,
    )
    depreciation_method: Mapped[DepreciationMethod] = mapped_column(
        Enum(
            DepreciationMethod,
            name="finance_asset_book_depreciation_method",
        ),
        nullable=False,
    )
    useful_life_months: Mapped[int] = mapped_column(
        nullable=False,
    )
    annual_rate_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 6),
        nullable=True,
    )
    residual_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    accumulated_depreciation: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    net_book_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    last_depreciation_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )


class FixedAssetTransaction(Base):
    __tablename__ = "finance_asset_transactions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "transaction_number",
            name="uq_finance_asset_transaction_tenant_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fixed_assets.id"),
        nullable=False,
    )
    transaction_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    transaction_type: Mapped[AssetTransactionType] = mapped_column(
        Enum(
            AssetTransactionType,
            name="finance_asset_transaction_type",
        ),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    from_location_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_asset_locations.id"),
        nullable=True,
    )
    to_location_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_asset_locations.id"),
        nullable=True,
    )
    journal_entry_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_journal_entries.id"),
        nullable=True,
    )
    reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )


class FixedAssetWarranty(Base):
    __tablename__ = "finance_asset_warranties"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fixed_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    warranty_number: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    starts_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    ends_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    terms: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )


class FixedAssetInsurance(Base):
    __tablename__ = "finance_asset_insurance"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fixed_assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    insurer_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    policy_number: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    coverage_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    premium_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    starts_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    ends_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )


class FixedAssetCapitalProject(Base):
    __tablename__ = "finance_asset_capital_projects"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "project_number",
            name="uq_finance_asset_project_tenant_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    project_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    status: Mapped[AssetProjectStatus] = mapped_column(
        Enum(
            AssetProjectStatus,
            name="finance_asset_project_status",
        ),
        nullable=False,
        default=AssetProjectStatus.DRAFT,
    )
    budget_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    accumulated_cost: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    cwip_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=False,
    )
    planned_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    planned_completion_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    actual_completion_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    capitalized_asset_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fixed_assets.id"),
        nullable=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )


class FixedAssetDisposal(Base):
    __tablename__ = "finance_asset_disposals"
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            name="uq_finance_asset_disposal_asset",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fixed_assets.id"),
        nullable=False,
    )
    disposal_type: Mapped[AssetDisposalType] = mapped_column(
        Enum(
            AssetDisposalType,
            name="finance_asset_disposal_type",
        ),
        nullable=False,
    )
    disposal_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    proceeds: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    disposal_costs: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    net_book_value: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    gain_loss: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    buyer_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    journal_entry_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_journal_entries.id"),
        nullable=True,
    )
    disposed_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )

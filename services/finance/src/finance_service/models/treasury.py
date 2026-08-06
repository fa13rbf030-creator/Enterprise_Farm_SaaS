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
    FraudCheckStatus,
    LiquidityForecastScenario,
    SettlementStatus,
    TreasuryApprovalDecision,
    TreasuryFileFormat,
    TreasuryPaymentBatchStatus,
    TreasuryPaymentItemStatus,
)
from finance_service.db.base import Base


class TreasuryPaymentBatch(Base):
    __tablename__ = "finance_treasury_payment_batches"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "batch_number",
            name="uq_finance_treasury_batch_tenant_number",
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
    batch_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    batch_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    execution_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    bank_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_bank_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    item_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    status: Mapped[TreasuryPaymentBatchStatus] = mapped_column(
        Enum(
            TreasuryPaymentBatchStatus,
            name="finance_treasury_batch_status",
        ),
        nullable=False,
        default=TreasuryPaymentBatchStatus.DRAFT,
    )
    file_format: Mapped[TreasuryFileFormat] = mapped_column(
        Enum(
            TreasuryFileFormat,
            name="finance_treasury_file_format",
        ),
        nullable=False,
        default=TreasuryFileFormat.ISO20022_PAIN_001,
    )
    payment_file_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    payment_file_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    external_submission_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    approved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    settled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TreasuryPaymentItem(Base):
    __tablename__ = "finance_treasury_payment_items"
    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "line_number",
            name="uq_finance_treasury_item_batch_line",
        ),
        UniqueConstraint(
            "tenant_id",
            "payment_reference",
            name="uq_finance_treasury_item_tenant_reference",
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
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_treasury_payment_batches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    vendor_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_vendors.id"),
        nullable=True,
    )
    vendor_payment_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_vendor_payments.id"),
        nullable=True,
    )
    payment_reference: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    beneficiary_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    beneficiary_account: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    beneficiary_iban: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    beneficiary_bank_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    status: Mapped[TreasuryPaymentItemStatus] = mapped_column(
        Enum(
            TreasuryPaymentItemStatus,
            name="finance_treasury_item_status",
        ),
        nullable=False,
        default=TreasuryPaymentItemStatus.PENDING,
    )
    fraud_check_status: Mapped[FraudCheckStatus] = mapped_column(
        Enum(
            FraudCheckStatus,
            name="finance_fraud_check_status",
        ),
        nullable=False,
        default=FraudCheckStatus.PASSED,
    )
    fraud_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    settlement_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    settlement_status: Mapped[SettlementStatus] = mapped_column(
        Enum(
            SettlementStatus,
            name="finance_settlement_status",
        ),
        nullable=False,
        default=SettlementStatus.PENDING,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )


class TreasuryBatchApproval(Base):
    __tablename__ = "finance_treasury_batch_approvals"
    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "approver_id",
            name="uq_finance_treasury_approval_batch_user",
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
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_treasury_payment_batches.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    approver_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    decision: Mapped[TreasuryApprovalDecision] = mapped_column(
        Enum(
            TreasuryApprovalDecision,
            name="finance_treasury_approval_decision",
        ),
        nullable=False,
    )
    comments: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        default="",
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class LiquidityForecast(Base):
    __tablename__ = "finance_liquidity_forecasts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "forecast_date",
            "currency_code",
            "scenario",
            name="uq_finance_liquidity_forecast_scope",
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
    forecast_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    horizon_days: Mapped[int] = mapped_column(
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    scenario: Mapped[LiquidityForecastScenario] = mapped_column(
        Enum(
            LiquidityForecastScenario,
            name="finance_liquidity_forecast_scenario",
        ),
        nullable=False,
    )
    opening_cash: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    expected_inflows: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    expected_outflows: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    projected_closing_cash: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    minimum_cash_buffer: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    funding_gap: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
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

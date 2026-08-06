from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from finance_service.core.enums import (
    FraudCheckStatus,
    LiquidityForecastScenario,
    SettlementStatus,
    TreasuryApprovalDecision,
    TreasuryFileFormat,
    TreasuryPaymentBatchStatus,
    TreasuryPaymentItemStatus,
)


class TreasuryPaymentItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_number: int = Field(ge=1)
    vendor_id: UUID | None = None
    vendor_payment_id: UUID | None = None
    payment_reference: str = Field(
        min_length=1,
        max_length=200,
    )
    beneficiary_name: str = Field(
        min_length=1,
        max_length=200,
    )
    beneficiary_account: str = Field(
        min_length=1,
        max_length=100,
    )
    beneficiary_iban: str | None = Field(
        default=None,
        max_length=100,
    )
    beneficiary_bank_code: str | None = Field(
        default=None,
        max_length=100,
    )
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )


class TreasuryPaymentBatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    batch_number: str = Field(
        min_length=1,
        max_length=100,
    )
    batch_date: date
    execution_date: date
    bank_account_id: UUID
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    file_format: TreasuryFileFormat = (
        TreasuryFileFormat.ISO20022_PAIN_001
    )
    created_by: UUID
    notes: str = Field(default="", max_length=2000)
    items: list[TreasuryPaymentItemCreate] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_batch(self):
        if self.execution_date < self.batch_date:
            raise ValueError(
                "Execution date cannot precede batch date"
            )

        line_numbers = [
            item.line_number
            for item in self.items
        ]

        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError(
                "Payment batch line numbers must be unique"
            )

        for item in self.items:
            if (
                item.currency_code.upper()
                != self.currency_code.upper()
            ):
                raise ValueError(
                    "Payment item currency must match batch"
                )

        return self


class TreasuryPaymentItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    line_number: int
    vendor_id: UUID | None
    vendor_payment_id: UUID | None
    payment_reference: str
    beneficiary_name: str
    beneficiary_account: str
    beneficiary_iban: str | None
    amount: Decimal
    currency_code: str
    status: TreasuryPaymentItemStatus
    fraud_check_status: FraudCheckStatus
    settlement_reference: str | None
    settlement_status: SettlementStatus


class TreasuryPaymentBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    batch_number: str
    batch_date: date
    execution_date: date
    bank_account_id: UUID
    currency_code: str
    total_amount: Decimal
    item_count: int
    status: TreasuryPaymentBatchStatus
    file_format: TreasuryFileFormat
    payment_file_name: str | None
    payment_file_hash: str | None
    external_submission_id: str | None
    created_by: UUID
    approved_by: UUID | None


class TreasuryPaymentBatchDetailRead(
    TreasuryPaymentBatchRead
):
    items: list[TreasuryPaymentItemRead]


class TreasuryBatchSubmitForApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    submitted_by: UUID


class TreasuryBatchApprovalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    approver_id: UUID
    decision: TreasuryApprovalDecision
    comments: str = Field(default="", max_length=1000)


class SettlementConfirmationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    settlement_reference: str = Field(
        min_length=1,
        max_length=200,
    )
    settlement_status: SettlementStatus
    failure_reason: str | None = Field(
        default=None,
        max_length=500,
    )


class LiquidityForecastCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    forecast_date: date
    horizon_days: int = Field(ge=1, le=365)
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    scenario: LiquidityForecastScenario
    opening_cash: Decimal
    expected_inflows: Decimal = Field(ge=0)
    expected_outflows: Decimal = Field(ge=0)
    minimum_cash_buffer: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    created_by: UUID


class LiquidityForecastRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    forecast_date: date
    horizon_days: int
    currency_code: str
    scenario: LiquidityForecastScenario
    opening_cash: Decimal
    expected_inflows: Decimal
    expected_outflows: Decimal
    projected_closing_cash: Decimal
    minimum_cash_buffer: Decimal
    funding_gap: Decimal


class TreasuryPaymentFileRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: UUID
    file_name: str
    file_format: TreasuryFileFormat
    sha256: str
    content: str


class TreasuryBatchSubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    submitted_by: UUID
    external_submission_id: str = Field(
        min_length=1,
        max_length=200,
    )


class TreasuryBatchApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    batch_id: UUID
    approver_id: UUID
    decision: TreasuryApprovalDecision
    comments: str


class TreasuryPaymentBatchFullRead(
    TreasuryPaymentBatchDetailRead
):
    approvals: list[TreasuryBatchApprovalRead]


class TreasuryFraudReviewRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: UUID
    passed: int
    review_required: int
    blocked: int
    can_submit_for_approval: bool


class TreasuryDashboardRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    draft_batches: int
    pending_approval_batches: int
    approved_batches: int
    submitted_batches: int
    settled_batches: int
    failed_batches: int
    total_pending_amount: Decimal
    total_submitted_amount: Decimal

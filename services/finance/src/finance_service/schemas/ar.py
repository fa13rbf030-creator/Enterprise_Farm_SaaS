from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from finance_service.core.enums import (
    CreditNoteStatus,
    CustomerStatus,
    InvoiceStatus,
    PaymentMethod,
    ReceiptStatus,
)


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    customer_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    billing_address: str = Field(default="", max_length=2000)
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    credit_limit: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    payment_terms_days: int = Field(default=0, ge=0)
    ar_control_account_id: UUID
    revenue_account_id: UUID
    tax_account_id: UUID | None = None
    is_tax_registered: bool = False
    tax_registration_number: str | None = Field(
        default=None,
        max_length=100,
    )


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_code: str
    name: str
    email: str | None
    phone: str | None
    billing_address: str
    currency_code: str
    credit_limit: Decimal
    payment_terms_days: int
    status: CustomerStatus
    ar_control_account_id: UUID
    revenue_account_id: UUID
    tax_account_id: UUID | None


class InvoiceLineCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_number: int = Field(ge=1)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    tax_rate: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
    )
    revenue_account_id: UUID


class InvoiceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    customer_id: UUID
    fiscal_period_id: UUID
    invoice_number: str = Field(
        min_length=1,
        max_length=100,
    )
    invoice_date: date
    due_date: date
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    exchange_rate: Decimal = Field(
        default=Decimal("1"),
        gt=0,
    )
    description: str = Field(default="", max_length=500)
    created_by: UUID
    lines: list[InvoiceLineCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_due_date(self):
        if self.due_date < self.invoice_date:
            raise ValueError(
                "Invoice due date cannot precede invoice date"
            )
        return self


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_id: UUID
    fiscal_period_id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    currency_code: str
    exchange_rate: Decimal
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    credited_amount: Decimal
    outstanding_amount: Decimal
    status: InvoiceStatus
    description: str
    journal_entry_id: UUID | None


class CreditNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    customer_id: UUID
    invoice_id: UUID | None = None
    fiscal_period_id: UUID
    credit_note_number: str = Field(
        min_length=1,
        max_length=100,
    )
    credit_note_date: date
    amount: Decimal = Field(gt=0)
    tax_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    reason: str = Field(min_length=1, max_length=500)
    created_by: UUID


class CreditNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_id: UUID
    invoice_id: UUID | None
    credit_note_number: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    applied_amount: Decimal
    status: CreditNoteStatus
    journal_entry_id: UUID | None


class ReceiptCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    customer_id: UUID
    fiscal_period_id: UUID
    receipt_number: str = Field(
        min_length=1,
        max_length=100,
    )
    receipt_date: date
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    exchange_rate: Decimal = Field(
        default=Decimal("1"),
        gt=0,
    )
    payment_method: PaymentMethod
    reference_number: str | None = Field(
        default=None,
        max_length=200,
    )
    bank_account_id: UUID | None = None
    created_by: UUID


class ReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_id: UUID
    receipt_number: str
    receipt_date: date
    amount: Decimal
    allocated_amount: Decimal
    unallocated_amount: Decimal
    payment_method: PaymentMethod
    status: ReceiptStatus
    journal_entry_id: UUID | None


class ReceiptAllocationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    invoice_id: UUID
    allocated_amount: Decimal = Field(gt=0)
    allocated_by: UUID


class AgingBucket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current: Decimal
    days_1_30: Decimal
    days_31_60: Decimal
    days_61_90: Decimal
    over_90: Decimal
    total: Decimal


class InvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    line_number: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal
    revenue_account_id: UUID


class InvoiceDetailRead(InvoiceRead):
    lines: list[InvoiceLineRead]


class CreditNoteApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    applied_by: UUID


class ReceiptPostRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    cash_account_id: UUID
    posted_by: UUID


class CustomerAgingRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    customer_id: UUID | None
    as_of_date: date
    current: Decimal
    days_1_30: Decimal
    days_31_60: Decimal
    days_61_90: Decimal
    over_90: Decimal
    total: Decimal


class CustomerStatementItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_type: str
    transaction_id: UUID
    transaction_number: str
    transaction_date: date
    debit: Decimal
    credit: Decimal
    balance: Decimal

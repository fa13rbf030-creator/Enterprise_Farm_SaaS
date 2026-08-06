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
    DebitNoteStatus,
    PaymentMethod,
    SupplierInvoiceStatus,
    VendorPaymentStatus,
    VendorStatus,
)


class VendorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    vendor_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    billing_address: str = Field(default="", max_length=2000)
    currency_code: str = Field(
        default="PKR",
        min_length=3,
        max_length=3,
    )
    payment_terms_days: int = Field(default=0, ge=0)
    credit_limit: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    ap_control_account_id: UUID
    default_expense_account_id: UUID
    input_tax_account_id: UUID | None = None
    withholding_tax_account_id: UUID | None = None
    is_tax_registered: bool = False
    tax_registration_number: str | None = Field(
        default=None,
        max_length=100,
    )


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vendor_code: str
    name: str
    email: str | None
    phone: str | None
    billing_address: str
    currency_code: str
    payment_terms_days: int
    credit_limit: Decimal
    status: VendorStatus
    ap_control_account_id: UUID
    default_expense_account_id: UUID
    input_tax_account_id: UUID | None
    withholding_tax_account_id: UUID | None


class SupplierInvoiceLineCreate(BaseModel):
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
    withholding_tax_rate: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
    )
    expense_account_id: UUID


class SupplierInvoiceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    vendor_id: UUID
    fiscal_period_id: UUID
    invoice_number: str = Field(
        min_length=1,
        max_length=100,
    )
    vendor_reference: str | None = Field(
        default=None,
        max_length=200,
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
    lines: list[SupplierInvoiceLineCreate] = Field(
        min_length=1
    )

    @model_validator(mode="after")
    def validate_due_date(self):
        if self.due_date < self.invoice_date:
            raise ValueError(
                "Supplier invoice due date cannot precede "
                "invoice date"
            )
        return self


class SupplierInvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    fiscal_period_id: UUID
    invoice_number: str
    vendor_reference: str | None
    invoice_date: date
    due_date: date
    currency_code: str
    exchange_rate: Decimal
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    withholding_tax_total: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    debited_amount: Decimal
    outstanding_amount: Decimal
    status: SupplierInvoiceStatus
    description: str
    journal_entry_id: UUID | None


class SupplierInvoiceLineRead(BaseModel):
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
    withholding_tax_rate: Decimal
    withholding_tax_amount: Decimal
    line_total: Decimal
    expense_account_id: UUID


class SupplierInvoiceDetailRead(SupplierInvoiceRead):
    lines: list[SupplierInvoiceLineRead]


class DebitNoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    vendor_id: UUID
    invoice_id: UUID | None = None
    fiscal_period_id: UUID
    debit_note_number: str = Field(
        min_length=1,
        max_length=100,
    )
    debit_note_date: date
    amount: Decimal = Field(gt=0)
    tax_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    reason: str = Field(min_length=1, max_length=500)
    created_by: UUID


class DebitNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    invoice_id: UUID | None
    debit_note_number: str
    amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    applied_amount: Decimal
    status: DebitNoteStatus
    journal_entry_id: UUID | None


class VendorPaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    vendor_id: UUID
    fiscal_period_id: UUID
    payment_number: str = Field(
        min_length=1,
        max_length=100,
    )
    payment_date: date
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
    cash_account_id: UUID
    created_by: UUID


class VendorPaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    payment_number: str
    payment_date: date
    amount: Decimal
    allocated_amount: Decimal
    unallocated_amount: Decimal
    payment_method: PaymentMethod
    cash_account_id: UUID
    status: VendorPaymentStatus
    journal_entry_id: UUID | None


class VendorPaymentAllocationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    invoice_id: UUID
    allocated_amount: Decimal = Field(gt=0)
    allocated_by: UUID


class PayablesAgingRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    vendor_id: UUID | None
    as_of_date: date
    current: Decimal
    days_1_30: Decimal
    days_31_60: Decimal
    days_61_90: Decimal
    over_90: Decimal
    total: Decimal

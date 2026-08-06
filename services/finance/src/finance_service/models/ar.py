from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
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
    CreditNoteStatus,
    CustomerStatus,
    InvoiceStatus,
    PaymentMethod,
    ReceiptStatus,
)
from finance_service.db.base import Base


class CustomerAccount(Base):
    __tablename__ = "finance_customers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "customer_code",
            name="uq_finance_customers_tenant_code",
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
    customer_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    billing_address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    payment_terms_days: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(
            CustomerStatus,
            name="finance_customer_status",
        ),
        nullable=False,
        default=CustomerStatus.ACTIVE,
    )
    ar_control_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    revenue_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    tax_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    is_tax_registered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    tax_registration_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class CustomerInvoice(Base):
    __tablename__ = "finance_customer_invoices"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "invoice_number",
            name="uq_finance_customer_invoices_tenant_number",
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
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    fiscal_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_fiscal_periods.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(24, 10),
        nullable=False,
        default=Decimal("1"),
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    discount_total: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    tax_total: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    credited_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    outstanding_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(
            InvoiceStatus,
            name="finance_invoice_status",
        ),
        nullable=False,
        default=InvoiceStatus.DRAFT,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    journal_entry_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_journal_entries.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CustomerInvoiceLine(Base):
    __tablename__ = "finance_customer_invoice_lines"
    __table_args__ = (
        UniqueConstraint(
            "invoice_id",
            "line_number",
            name="uq_finance_customer_invoice_lines_number",
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
    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_customer_invoices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(12, 6),
        nullable=False,
        default=Decimal("0"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    revenue_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )


class CustomerCreditNote(Base):
    __tablename__ = "finance_customer_credit_notes"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "credit_note_number",
            name=(
                "uq_finance_customer_credit_notes_"
                "tenant_number"
            ),
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
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_customers.id"),
        nullable=False,
    )
    invoice_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_customer_invoices.id"),
        nullable=True,
    )
    fiscal_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fiscal_periods.id"),
        nullable=False,
    )
    credit_note_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    credit_note_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    applied_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[CreditNoteStatus] = mapped_column(
        Enum(
            CreditNoteStatus,
            name="finance_credit_note_status",
        ),
        nullable=False,
        default=CreditNoteStatus.DRAFT,
    )
    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    journal_entry_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_journal_entries.id"),
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


class CustomerReceipt(Base):
    __tablename__ = "finance_customer_receipts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "receipt_number",
            name=(
                "uq_finance_customer_receipts_"
                "tenant_number"
            ),
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
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_customers.id"),
        nullable=False,
        index=True,
    )
    fiscal_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fiscal_periods.id"),
        nullable=False,
    )
    receipt_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    receipt_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    unallocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(24, 10),
        nullable=False,
        default=Decimal("1"),
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(
            PaymentMethod,
            name="finance_payment_method",
        ),
        nullable=False,
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    bank_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    status: Mapped[ReceiptStatus] = mapped_column(
        Enum(
            ReceiptStatus,
            name="finance_receipt_status",
        ),
        nullable=False,
        default=ReceiptStatus.DRAFT,
    )
    journal_entry_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_journal_entries.id"),
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


class ReceiptAllocation(Base):
    __tablename__ = "finance_receipt_allocations"
    __table_args__ = (
        UniqueConstraint(
            "receipt_id",
            "invoice_id",
            name=(
                "uq_finance_receipt_allocations_"
                "receipt_invoice"
            ),
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
    receipt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_customer_receipts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_customer_invoices.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    allocated_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    allocated_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

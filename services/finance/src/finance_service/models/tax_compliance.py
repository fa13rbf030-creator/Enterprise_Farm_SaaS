from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.db.base import Base


class TaxType(str, __import__("enum").Enum):
    SALES_TAX = "sales_tax"
    VAT = "vat"
    GST = "gst"
    WITHHOLDING = "withholding"
    INCOME_TAX = "income_tax"
    EXCISE = "excise"
    CUSTOMS = "customs"
    OTHER = "other"


class TaxReturnStatus(str, __import__("enum").Enum):
    DRAFT = "draft"
    PREPARED = "prepared"
    REVIEWED = "reviewed"
    FILED = "filed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    AMENDED = "amended"
    CANCELLED = "cancelled"


class StatutoryFilingStatus(str, __import__("enum").Enum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    OVERDUE = "overdue"


class TaxJurisdiction(Base):
    __tablename__ = "finance_tax_jurisdictions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "jurisdiction_code",
            name="uq_finance_tax_jurisdiction_code",
        ),
        Index(
            "ix_finance_tax_jurisdiction_tenant",
            "tenant_id",
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
    )
    jurisdiction_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    jurisdiction_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    country_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )
    region_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    authority_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    authority_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TaxRegistration(Base):
    __tablename__ = "finance_tax_registrations"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "registration_number",
            name="uq_finance_tax_registration_number",
        ),
        Index(
            "ix_finance_tax_registration_tenant",
            "tenant_id",
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
    )
    jurisdiction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_tax_jurisdictions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    registration_number: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    legal_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class TaxCode(Base):
    __tablename__ = "finance_tax_codes"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "tax_code",
            name="uq_finance_tax_code",
        ),
        Index(
            "ix_finance_tax_code_tenant",
            "tenant_id",
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
    )
    jurisdiction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_tax_jurisdictions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    tax_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    tax_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    tax_type: Mapped[TaxType] = mapped_column(
        Enum(
            TaxType,
            name="finance_tax_type",
        ),
        nullable=False,
    )
    input_tax_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=True,
    )
    output_tax_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=True,
    )
    payable_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=True,
    )
    recoverable_account_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_ledger_accounts.id"),
        nullable=True,
    )
    is_recoverable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class TaxRate(Base):
    __tablename__ = "finance_tax_rates"

    __table_args__ = (
        UniqueConstraint(
            "tax_code_id",
            "effective_from",
            name="uq_finance_tax_rate_effective_date",
        ),
        CheckConstraint(
            "rate >= 0 AND rate <= 100",
            name="ck_finance_tax_rate_percentage",
        ),
        Index(
            "ix_finance_tax_rate_tenant",
            "tenant_id",
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
    )
    tax_code_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_tax_codes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    rate: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )


class WithholdingTaxRule(Base):
    __tablename__ = "finance_withholding_tax_rules"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "rule_code",
            name="uq_finance_withholding_rule_code",
        ),
        CheckConstraint(
            "rate >= 0 AND rate <= 100",
            name="ck_finance_withholding_rate",
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
    jurisdiction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_tax_jurisdictions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    rule_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    rule_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    rate: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
    )
    threshold_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class TaxPeriod(Base):
    __tablename__ = "finance_tax_periods"

    __table_args__ = (
        UniqueConstraint(
            "registration_id",
            "period_start",
            "period_end",
            name="uq_finance_tax_period_range",
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_finance_tax_period_range",
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
    registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_tax_registrations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    period_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    filing_due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    payment_due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


class TaxReturn(Base):
    __tablename__ = "finance_tax_returns"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "return_number",
            name="uq_finance_tax_return_number",
        ),
        Index(
            "ix_finance_tax_return_tenant_status",
            "tenant_id",
            "status",
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
    )
    tax_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_tax_periods.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    return_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[TaxReturnStatus] = mapped_column(
        Enum(
            TaxReturnStatus,
            name="finance_tax_return_status",
        ),
        nullable=False,
        default=TaxReturnStatus.DRAFT,
    )
    output_tax: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    input_tax: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    withholding_tax: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    adjustments: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    credits: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    net_tax_liability: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    prepared_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    filed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    filed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    authority_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


class StatutoryFiling(Base):
    __tablename__ = "finance_statutory_filings"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "filing_number",
            name="uq_finance_statutory_filing_number",
        ),
        Index(
            "ix_finance_statutory_filing_tenant_status",
            "tenant_id",
            "status",
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
    )
    tax_return_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_tax_returns.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    filing_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    filing_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    status: Mapped[StatutoryFilingStatus] = mapped_column(
        Enum(
            StatutoryFilingStatus,
            name="finance_statutory_filing_status",
        ),
        nullable=False,
        default=StatutoryFilingStatus.DRAFT,
    )
    document_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    submission_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    submitted_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

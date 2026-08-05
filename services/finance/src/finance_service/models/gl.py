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
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.core.enums import (
    AccountStatus,
    AccountType,
    FiscalPeriodStatus,
    JournalSource,
    JournalStatus,
    NormalBalance,
)
from finance_service.db.base import Base


class LedgerAccount(Base):
    __tablename__ = "finance_ledger_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "code",
            name="uq_finance_ledger_accounts_tenant_code",
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
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(
        String(50),
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
    account_type: Mapped[AccountType] = mapped_column(
        Enum(
            AccountType,
            name="finance_account_type",
        ),
        nullable=False,
    )
    normal_balance: Mapped[NormalBalance] = mapped_column(
        Enum(
            NormalBalance,
            name="finance_normal_balance",
        ),
        nullable=False,
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(
            AccountStatus,
            name="finance_account_status",
        ),
        nullable=False,
        default=AccountStatus.ACTIVE,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    is_control_account: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    allows_manual_posting: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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


class FiscalYear(Base):
    __tablename__ = "finance_fiscal_years"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_finance_fiscal_years_tenant_name",
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
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    starts_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    ends_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class FiscalPeriod(Base):
    __tablename__ = "finance_fiscal_periods"
    __table_args__ = (
        UniqueConstraint(
            "fiscal_year_id",
            "period_number",
            name="uq_finance_fiscal_periods_year_number",
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
    fiscal_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_fiscal_years.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    period_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    starts_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    ends_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    status: Mapped[FiscalPeriodStatus] = mapped_column(
        Enum(
            FiscalPeriodStatus,
            name="finance_fiscal_period_status",
        ),
        nullable=False,
        default=FiscalPeriodStatus.OPEN,
    )


class JournalEntry(Base):
    __tablename__ = "finance_journal_entries"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "journal_number",
            name="uq_finance_journal_entries_tenant_number",
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
    fiscal_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_fiscal_periods.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    journal_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    entry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    source: Mapped[JournalSource] = mapped_column(
        Enum(
            JournalSource,
            name="finance_journal_source",
        ),
        nullable=False,
        default=JournalSource.MANUAL,
    )
    source_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[JournalStatus] = mapped_column(
        Enum(
            JournalStatus,
            name="finance_journal_status",
        ),
        nullable=False,
        default=JournalStatus.DRAFT,
    )
    total_debit: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    total_credit: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    posted_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    reversal_of_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_journal_entries.id",
            ondelete="RESTRICT",
        ),
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


class JournalLine(Base):
    __tablename__ = "finance_journal_lines"
    __table_args__ = (
        UniqueConstraint(
            "journal_entry_id",
            "line_number",
            name="uq_finance_journal_lines_entry_number",
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
    journal_entry_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_journal_entries.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    ledger_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    debit: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    credit: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
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
    base_debit: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    base_credit: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )

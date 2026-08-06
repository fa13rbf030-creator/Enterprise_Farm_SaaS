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
    BankAccountStatus,
    BankAccountType,
    BankStatementLineType,
    BankStatementStatus,
    ReconciliationMatchType,
    ReconciliationStatus,
)
from finance_service.db.base import Base


class BankAccount(Base):
    __tablename__ = "finance_bank_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "account_code",
            name="uq_finance_bank_accounts_tenant_code",
        ),
        UniqueConstraint(
            "tenant_id",
            "iban",
            name="uq_finance_bank_accounts_tenant_iban",
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
    account_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    account_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    bank_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    branch_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="",
    )
    branch_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    account_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    iban: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    swift_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="PKR",
    )
    account_type: Mapped[BankAccountType] = mapped_column(
        Enum(
            BankAccountType,
            name="finance_bank_account_type",
        ),
        nullable=False,
    )
    status: Mapped[BankAccountStatus] = mapped_column(
        Enum(
            BankAccountStatus,
            name="finance_bank_account_status",
        ),
        nullable=False,
        default=BankAccountStatus.ACTIVE,
    )
    ledger_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class BankStatement(Base):
    __tablename__ = "finance_bank_statements"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "bank_account_id",
            "statement_number",
            name=(
                "uq_finance_bank_statements_"
                "tenant_account_number"
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
    bank_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_bank_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    statement_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    statement_date: Mapped[date] = mapped_column(
        Date,
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
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    closing_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    total_credits: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    total_debits: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[BankStatementStatus] = mapped_column(
        Enum(
            BankStatementStatus,
            name="finance_bank_statement_status",
        ),
        nullable=False,
        default=BankStatementStatus.DRAFT,
    )
    source_file_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    imported_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class BankStatementLine(Base):
    __tablename__ = "finance_bank_statement_lines"
    __table_args__ = (
        UniqueConstraint(
            "statement_id",
            "line_number",
            name=(
                "uq_finance_bank_statement_lines_"
                "statement_number"
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
    statement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_bank_statements.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    value_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    line_type: Mapped[BankStatementLineType] = mapped_column(
        Enum(
            BankStatementLineType,
            name="finance_bank_statement_line_type",
        ),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    running_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(24, 6),
        nullable=True,
    )
    is_reconciled: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    matched_journal_entry_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_journal_entries.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )


class BankReconciliation(Base):
    __tablename__ = "finance_bank_reconciliations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "bank_account_id",
            "statement_id",
            name=(
                "uq_finance_bank_reconciliations_"
                "tenant_account_statement"
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
    bank_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_bank_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    statement_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_bank_statements.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    reconciliation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    book_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    statement_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    reconciled_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    difference_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    status: Mapped[ReconciliationStatus] = mapped_column(
        Enum(
            ReconciliationStatus,
            name="finance_reconciliation_status",
        ),
        nullable=False,
        default=ReconciliationStatus.DRAFT,
    )
    started_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    completed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
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


class BankReconciliationMatch(Base):
    __tablename__ = "finance_bank_reconciliation_matches"
    __table_args__ = (
        UniqueConstraint(
            "reconciliation_id",
            "statement_line_id",
            name=(
                "uq_finance_bank_reconciliation_matches_"
                "reconciliation_line"
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
    reconciliation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_bank_reconciliations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    statement_line_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_bank_statement_lines.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    journal_entry_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_journal_entries.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    match_type: Mapped[ReconciliationMatchType] = mapped_column(
        Enum(
            ReconciliationMatchType,
            name="finance_reconciliation_match_type",
        ),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
    )
    matched_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

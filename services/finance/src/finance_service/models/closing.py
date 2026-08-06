from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.core.enums import (
    FiscalYearCloseStatus,
    OpeningBalanceStatus,
)
from finance_service.db.base import Base


class OpeningBalanceBatch(Base):
    __tablename__ = "finance_opening_balance_batches"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "batch_number",
            name=(
                "uq_finance_opening_balance_batches_"
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
    fiscal_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_fiscal_periods.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    batch_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    status: Mapped[OpeningBalanceStatus] = mapped_column(
        Enum(
            OpeningBalanceStatus,
            name="finance_opening_balance_status",
        ),
        nullable=False,
        default=OpeningBalanceStatus.DRAFT,
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
    validated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    posted_journal_id: Mapped[UUID | None] = mapped_column(
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


class OpeningBalanceLine(Base):
    __tablename__ = "finance_opening_balance_lines"
    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "ledger_account_id",
            name=(
                "uq_finance_opening_balance_lines_"
                "batch_account"
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
    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_opening_balance_batches.id",
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
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )


class FiscalYearCloseRun(Base):
    __tablename__ = "finance_fiscal_year_close_runs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "fiscal_year_id",
            name=(
                "uq_finance_fiscal_year_close_runs_"
                "tenant_year"
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
    fiscal_year_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_fiscal_years.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    retained_earnings_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_ledger_accounts.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    closing_journal_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_journal_entries.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    status: Mapped[FiscalYearCloseStatus] = mapped_column(
        Enum(
            FiscalYearCloseStatus,
            name="finance_fiscal_year_close_status",
        ),
        nullable=False,
        default=FiscalYearCloseStatus.OPEN,
    )
    net_income: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    started_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

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

from finance_service.core.enums import (
    FinancialCloseCycleType,
    FinancialCloseExceptionSeverity,
    FinancialCloseExceptionStatus,
    FinancialCloseSignOffRole,
    FinancialCloseStatus,
    FinancialCloseTaskStatus,
    FinancialCloseTaskType,
    PeriodLockType,
)
from finance_service.db.base import Base


class FinancialCloseCycle(Base):
    __tablename__ = "finance_close_cycles"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "cycle_code",
            name="uq_finance_close_cycle_tenant_code",
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_finance_close_cycle_valid_period",
        ),
        Index(
            "ix_finance_close_cycle_tenant",
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
        index=True,
    )
    cycle_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    cycle_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    cycle_type: Mapped[FinancialCloseCycleType] = mapped_column(
        Enum(
            FinancialCloseCycleType,
            name="finance_close_cycle_type",
        ),
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
    fiscal_period_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fiscal_periods.id"),
        nullable=True,
    )
    consolidation_period_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_consolidation_periods.id"),
        nullable=True,
    )
    status: Mapped[FinancialCloseStatus] = mapped_column(
        Enum(
            FinancialCloseStatus,
            name="finance_close_status",
        ),
        nullable=False,
        default=FinancialCloseStatus.DRAFT,
    )
    materiality_threshold: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    planned_close_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    actual_close_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    opened_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    closed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
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


class FinancialCloseTask(Base):
    __tablename__ = "finance_close_tasks"

    __table_args__ = (
        UniqueConstraint(
            "cycle_id",
            "task_code",
            name="uq_finance_close_task_cycle_code",
        ),
        Index(
            "ix_finance_close_task_tenant",
            "tenant_id",
        ),
        Index(
            "ix_finance_close_task_cycle_status",
            "cycle_id",
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
    cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_close_cycles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    task_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    task_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    task_type: Mapped[FinancialCloseTaskType] = mapped_column(
        Enum(
            FinancialCloseTaskType,
            name="finance_close_task_type",
        ),
        nullable=False,
    )
    status: Mapped[FinancialCloseTaskStatus] = mapped_column(
        Enum(
            FinancialCloseTaskStatus,
            name="finance_close_task_status",
        ),
        nullable=False,
        default=FinancialCloseTaskStatus.NOT_STARTED,
    )
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    reviewer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    evidence_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class FinancialCloseTaskDependency(Base):
    __tablename__ = "finance_close_task_dependencies"

    __table_args__ = (
        UniqueConstraint(
            "task_id",
            "depends_on_task_id",
            name="uq_finance_close_task_dependency",
        ),
        CheckConstraint(
            "task_id <> depends_on_task_id",
            name="no_self_dependency",
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
    task_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_close_tasks.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    depends_on_task_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_close_tasks.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )


class FinancialCloseException(Base):
    __tablename__ = "finance_close_exceptions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "exception_number",
            name="uq_finance_close_exception_number",
        ),
        Index(
            "ix_finance_close_exception_cycle_status",
            "cycle_id",
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
        index=True,
    )
    cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_close_cycles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    task_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_close_tasks.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    exception_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    severity: Mapped[FinancialCloseExceptionSeverity] = mapped_column(
        Enum(
            FinancialCloseExceptionSeverity,
            name="finance_close_exception_severity",
        ),
        nullable=False,
    )
    status: Mapped[FinancialCloseExceptionStatus] = mapped_column(
        Enum(
            FinancialCloseExceptionStatus,
            name="finance_close_exception_status",
        ),
        nullable=False,
        default=FinancialCloseExceptionStatus.OPEN,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    is_material: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    assigned_to: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    resolved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    resolution_notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class FinancialCloseSignOff(Base):
    __tablename__ = "finance_close_signoffs"

    __table_args__ = (
        UniqueConstraint(
            "cycle_id",
            "role",
            name="uq_finance_close_signoff_cycle_role",
        ),
        Index(
            "ix_finance_close_signoff_tenant",
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
    cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_close_cycles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    role: Mapped[FinancialCloseSignOffRole] = mapped_column(
        Enum(
            FinancialCloseSignOffRole,
            name="finance_close_signoff_role",
        ),
        nullable=False,
    )
    signer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    comments: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )


class FinancialPeriodLock(Base):
    __tablename__ = "finance_period_locks"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "fiscal_period_id",
            "lock_type",
            name="uq_finance_period_lock_scope",
        ),
        Index(
            "ix_finance_period_lock_tenant",
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
    fiscal_period_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("finance_fiscal_periods.id"),
        nullable=False,
    )
    cycle_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_close_cycles.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    lock_type: Mapped[PeriodLockType] = mapped_column(
        Enum(
            PeriodLockType,
            name="finance_period_lock_type",
        ),
        nullable=False,
    )
    locked_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    locked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    unlocked_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    unlocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class FinancialCloseAuditPackage(Base):
    __tablename__ = "finance_close_audit_packages"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "package_number",
            name="uq_finance_close_audit_package_number",
        ),
        Index(
            "ix_finance_close_audit_package_tenant",
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
    cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_close_cycles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    package_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    generated_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    document_reference: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    package_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

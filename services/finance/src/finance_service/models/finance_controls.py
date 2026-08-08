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
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from finance_service.db.base import Base


class FinanceControlType(str, __import__("enum").Enum):
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"
    GOVERNANCE = "governance"


class FinanceControlFrequency(str, __import__("enum").Enum):
    TRANSACTION = "transaction"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    EVENT_DRIVEN = "event_driven"


class FinanceControlStatus(str, __import__("enum").Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class FinanceControlExecutionStatus(str, __import__("enum").Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    EXCEPTION = "exception"
    WAIVED = "waived"


class FinanceControlExceptionStatus(str, __import__("enum").Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    REMEDIATED = "remediated"
    WAIVED = "waived"
    CLOSED = "closed"


class FinanceControlSeverity(str, __import__("enum").Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReconciliationStatus(str, __import__("enum").Enum):
    DRAFT = "draft"
    RUNNING = "running"
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    REVIEWED = "reviewed"
    CLOSED = "closed"


class AttestationStatus(str, __import__("enum").Enum):
    PENDING = "pending"
    ATTESTED = "attested"
    REJECTED = "rejected"
    EXPIRED = "expired"


class FinanceControlDefinition(Base):
    __tablename__ = "finance_control_definitions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "control_code",
            name="uq_finance_control_definition_code",
        ),
        Index(
            "ix_finance_control_definition_tenant",
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
    control_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    control_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    control_type: Mapped[FinanceControlType] = mapped_column(
        Enum(
            FinanceControlType,
            name="finance_control_type",
        ),
        nullable=False,
    )
    frequency: Mapped[FinanceControlFrequency] = mapped_column(
        Enum(
            FinanceControlFrequency,
            name="finance_control_frequency",
        ),
        nullable=False,
    )
    status: Mapped[FinanceControlStatus] = mapped_column(
        Enum(
            FinanceControlStatus,
            name="finance_control_status",
        ),
        nullable=False,
        default=FinanceControlStatus.DRAFT,
    )
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    reviewer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    module_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    risk_statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    control_objective: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    procedure_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    is_key_control: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    inherent_risk_score: Mapped[Decimal] = mapped_column(
        Numeric(9, 2),
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class FinanceControlExecution(Base):
    __tablename__ = "finance_control_executions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "execution_number",
            name="uq_finance_control_execution_number",
        ),
        Index(
            "ix_finance_control_execution_control_status",
            "control_id",
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
    control_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_control_definitions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    execution_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    execution_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    status: Mapped[FinanceControlExecutionStatus] = mapped_column(
        Enum(
            FinanceControlExecutionStatus,
            name="finance_control_execution_status",
        ),
        nullable=False,
        default=FinanceControlExecutionStatus.PENDING,
    )
    tested_population: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    passed_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    failed_checks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    effectiveness_percentage: Mapped[Decimal] = mapped_column(
        Numeric(9, 2),
        nullable=False,
        default=Decimal("0"),
    )
    residual_risk_score: Mapped[Decimal] = mapped_column(
        Numeric(9, 2),
        nullable=False,
        default=Decimal("0"),
    )
    executed_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
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
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )


class FinanceSoDViolation(Base):
    __tablename__ = "finance_sod_violations"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "violation_number",
            name="uq_finance_sod_violation_number",
        ),
        Index(
            "ix_finance_sod_violation_tenant_status",
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
    violation_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    module_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    conflicting_action_a: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    conflicting_action_b: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    severity: Mapped[FinanceControlSeverity] = mapped_column(
        Enum(
            FinanceControlSeverity,
            name="finance_control_severity",
        ),
        nullable=False,
    )
    status: Mapped[FinanceControlExceptionStatus] = mapped_column(
        Enum(
            FinanceControlExceptionStatus,
            name="finance_sod_violation_status",
        ),
        nullable=False,
        default=FinanceControlExceptionStatus.OPEN,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    remediated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    remediated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    remediation_notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )


class FinanceReconciliationRun(Base):
    __tablename__ = "finance_reconciliation_runs"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "reconciliation_number",
            name="uq_finance_reconciliation_number",
        ),
        Index(
            "ix_finance_reconciliation_tenant_status",
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
    reconciliation_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    reconciliation_type: Mapped[str] = mapped_column(
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
    source_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    target_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    source_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    target_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    variance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    tolerance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[ReconciliationStatus] = mapped_column(
        Enum(
            ReconciliationStatus,
            name="finance_control_reconciliation_status",
        ),
        nullable=False,
        default=ReconciliationStatus.DRAFT,
    )
    prepared_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class FinanceControlException(Base):
    __tablename__ = "finance_control_exceptions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "exception_number",
            name="uq_finance_control_exception_number",
        ),
        Index(
            "ix_finance_control_exception_tenant_status",
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
    execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_control_executions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    reconciliation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_reconciliation_runs.id",
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
    severity: Mapped[FinanceControlSeverity] = mapped_column(
        Enum(
            FinanceControlSeverity,
            name="finance_control_exception_severity",
        ),
        nullable=False,
    )
    status: Mapped[FinanceControlExceptionStatus] = mapped_column(
        Enum(
            FinanceControlExceptionStatus,
            name="finance_control_exception_status",
        ),
        nullable=False,
        default=FinanceControlExceptionStatus.OPEN,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        nullable=False,
        default=Decimal("0"),
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    remediation_notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class FinanceControlAttestation(Base):
    __tablename__ = "finance_control_attestations"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "attestation_number",
            name="uq_finance_control_attestation_number",
        ),
        Index(
            "ix_finance_control_attestation_tenant",
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
    control_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_control_definitions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    attestation_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    attestation_period: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    attestor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    status: Mapped[AttestationStatus] = mapped_column(
        Enum(
            AttestationStatus,
            name="finance_control_attestation_status",
        ),
        nullable=False,
        default=AttestationStatus.PENDING,
    )
    attested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    comments: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )


class FinanceAuditEvidence(Base):
    __tablename__ = "finance_audit_evidence"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "evidence_number",
            name="uq_finance_audit_evidence_number",
        ),
        Index(
            "ix_finance_audit_evidence_tenant",
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
    control_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_control_definitions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    execution_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "finance_control_executions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    evidence_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    evidence_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    document_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    content_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    collected_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

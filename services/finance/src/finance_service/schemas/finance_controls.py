from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from finance_service.models.finance_controls import (
    AttestationStatus,
    FinanceControlExceptionStatus,
    FinanceControlExecutionStatus,
    FinanceControlFrequency,
    FinanceControlSeverity,
    FinanceControlStatus,
    FinanceControlType,
    ReconciliationStatus,
)


class FinanceControlDefinitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    control_code: str = Field(min_length=1, max_length=100)
    control_name: str = Field(min_length=1, max_length=255)
    control_type: FinanceControlType
    frequency: FinanceControlFrequency
    owner_id: UUID
    reviewer_id: UUID | None = None
    module_name: str = Field(min_length=1, max_length=100)
    risk_statement: str = Field(default="", max_length=4000)
    control_objective: str = Field(default="", max_length=4000)
    procedure_description: str = Field(default="", max_length=4000)
    is_key_control: bool = False
    inherent_risk_score: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
    )
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "Control end cannot precede start"
            )
        return self


class FinanceControlDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    control_code: str
    control_name: str
    control_type: FinanceControlType
    frequency: FinanceControlFrequency
    status: FinanceControlStatus
    owner_id: UUID
    reviewer_id: UUID | None
    module_name: str
    risk_statement: str
    control_objective: str
    procedure_description: str
    is_key_control: bool
    inherent_risk_score: Decimal
    effective_from: date
    effective_to: date | None


class FinanceControlExecutionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    control_id: UUID
    execution_number: str = Field(min_length=1, max_length=100)
    execution_date: date
    tested_population: int = Field(ge=0)
    passed_checks: int = Field(ge=0)
    failed_checks: int = Field(ge=0)
    executed_by: UUID
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validate_counts(self):
        if (
            self.passed_checks + self.failed_checks
            > self.tested_population
        ):
            raise ValueError(
                "Passed and failed checks cannot exceed tested population"
            )
        return self


class FinanceControlExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    control_id: UUID
    execution_number: str
    execution_date: date
    status: FinanceControlExecutionStatus
    tested_population: int
    passed_checks: int
    failed_checks: int
    effectiveness_percentage: Decimal
    residual_risk_score: Decimal
    executed_by: UUID
    reviewed_by: UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    notes: str


class FinanceReconciliationRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    reconciliation_number: str = Field(
        min_length=1,
        max_length=100,
    )
    reconciliation_type: str = Field(
        min_length=1,
        max_length=100,
    )
    period_start: date
    period_end: date
    source_reference: str = Field(min_length=1, max_length=255)
    target_reference: str = Field(min_length=1, max_length=255)
    source_balance: Decimal
    target_balance: Decimal
    tolerance: Decimal = Field(default=Decimal("0"), ge=0)
    prepared_by: UUID

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError(
                "Reconciliation period end cannot precede start"
            )
        return self


class FinanceReconciliationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    reconciliation_number: str
    reconciliation_type: str
    period_start: date
    period_end: date
    source_reference: str
    target_reference: str
    source_balance: Decimal
    target_balance: Decimal
    variance: Decimal
    tolerance: Decimal
    status: ReconciliationStatus
    prepared_by: UUID
    reviewed_by: UUID | None
    completed_at: datetime | None


class FinanceControlExceptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    execution_id: UUID | None = None
    reconciliation_id: UUID | None = None
    exception_number: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=4000)
    severity: FinanceControlSeverity
    amount: Decimal = Decimal("0")
    owner_id: UUID | None = None
    due_date: date | None = None


class FinanceControlExceptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    execution_id: UUID | None
    reconciliation_id: UUID | None
    exception_number: str
    title: str
    description: str
    severity: FinanceControlSeverity
    status: FinanceControlExceptionStatus
    amount: Decimal
    owner_id: UUID | None
    due_date: date | None
    remediation_notes: str
    created_at: datetime


class FinanceControlAttestationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    control_id: UUID
    attestation_number: str = Field(min_length=1, max_length=100)
    attestation_period: str = Field(min_length=1, max_length=100)
    attestor_id: UUID
    comments: str = Field(default="", max_length=4000)


class FinanceControlAttestationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    control_id: UUID
    attestation_number: str
    attestation_period: str
    attestor_id: UUID
    status: AttestationStatus
    attested_at: datetime | None
    comments: str


class FinanceAuditEvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    control_id: UUID | None = None
    execution_id: UUID | None = None
    evidence_number: str = Field(min_length=1, max_length=100)
    evidence_type: str = Field(min_length=1, max_length=100)
    document_reference: str | None = Field(
        default=None,
        max_length=500,
    )
    content_hash: str | None = Field(
        default=None,
        max_length=128,
    )
    collected_by: UUID
    notes: str = Field(default="", max_length=4000)


class FinanceAuditEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    control_id: UUID | None
    execution_id: UUID | None
    evidence_number: str
    evidence_type: str
    document_reference: str | None
    content_hash: str | None
    collected_by: UUID
    collected_at: datetime
    notes: str

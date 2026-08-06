from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class FinancialCloseTaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_code: str = Field(min_length=1, max_length=100)
    task_name: str = Field(min_length=1, max_length=255)
    task_type: FinancialCloseTaskType
    owner_id: UUID
    reviewer_id: UUID | None = None
    due_date: date | None = None
    evidence_reference: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str = Field(default="", max_length=4000)
    is_mandatory: bool = True


class FinancialCloseCycleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    cycle_code: str = Field(min_length=1, max_length=100)
    cycle_name: str = Field(min_length=1, max_length=255)
    cycle_type: FinancialCloseCycleType
    period_start: date
    period_end: date
    fiscal_period_id: UUID | None = None
    consolidation_period_id: UUID | None = None
    materiality_threshold: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    planned_close_date: date | None = None
    opened_by: UUID
    description: str = Field(default="", max_length=4000)
    tasks: list[FinancialCloseTaskCreate] = Field(
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_cycle(self):
        if self.period_end < self.period_start:
            raise ValueError(
                "Close period end cannot precede start"
            )

        if (
            self.planned_close_date is not None
            and self.planned_close_date < self.period_end
        ):
            raise ValueError(
                "Planned close date cannot precede period end"
            )

        task_codes = [task.task_code for task in self.tasks]

        if len(task_codes) != len(set(task_codes)):
            raise ValueError(
                "Close task codes must be unique"
            )

        return self


class FinancialCloseCycleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_code: str
    cycle_name: str
    cycle_type: FinancialCloseCycleType
    period_start: date
    period_end: date
    fiscal_period_id: UUID | None
    consolidation_period_id: UUID | None
    status: FinancialCloseStatus
    materiality_threshold: Decimal
    planned_close_date: date | None
    actual_close_date: date | None
    opened_by: UUID
    closed_by: UUID | None
    description: str


class FinancialCloseTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    task_code: str
    task_name: str
    task_type: FinancialCloseTaskType
    status: FinancialCloseTaskStatus
    owner_id: UUID
    reviewer_id: UUID | None
    due_date: date | None
    started_at: datetime | None
    completed_at: datetime | None
    approved_at: datetime | None
    evidence_reference: str | None
    notes: str
    is_mandatory: bool


class FinancialCloseTaskStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    status: FinancialCloseTaskStatus
    actor_id: UUID
    evidence_reference: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str = Field(default="", max_length=4000)


class FinancialCloseExceptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    cycle_id: UUID
    task_id: UUID | None = None
    exception_number: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=4000)
    severity: FinancialCloseExceptionSeverity
    amount: Decimal = Decimal("0")
    assigned_to: UUID | None = None


class FinancialCloseExceptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    task_id: UUID | None
    exception_number: str
    title: str
    description: str
    severity: FinancialCloseExceptionSeverity
    status: FinancialCloseExceptionStatus
    amount: Decimal
    is_material: bool
    assigned_to: UUID | None
    resolved_by: UUID | None
    resolution_notes: str
    created_at: datetime
    resolved_at: datetime | None


class FinancialCloseSignOffCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    cycle_id: UUID
    role: FinancialCloseSignOffRole
    signer_id: UUID
    comments: str = Field(default="", max_length=4000)


class FinancialCloseSignOffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    role: FinancialCloseSignOffRole
    signer_id: UUID
    signed_at: datetime
    comments: str


class FinancialPeriodLockCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    fiscal_period_id: UUID
    cycle_id: UUID | None = None
    lock_type: PeriodLockType
    locked_by: UUID
    reason: str = Field(default="", max_length=4000)


class FinancialPeriodUnlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    unlocked_by: UUID
    reason: str = Field(default="", max_length=4000)


class FinancialPeriodLockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    fiscal_period_id: UUID
    cycle_id: UUID | None
    lock_type: PeriodLockType
    locked_by: UUID
    locked_at: datetime
    unlocked_by: UUID | None
    unlocked_at: datetime | None
    reason: str
    is_active: bool

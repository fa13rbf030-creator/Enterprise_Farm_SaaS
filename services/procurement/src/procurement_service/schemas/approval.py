from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    ApprovalStepStatus,
)


class ApprovalSchemaBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class ProcurementApprovalStepCreate(ApprovalSchemaBase):
    step_number: int = Field(gt=0)
    approver_id: UUID | None = None


class ProcurementApprovalRequestCreate(ApprovalSchemaBase):
    object_type: ApprovalObjectType
    object_id: UUID
    requested_by: UUID
    comments: str | None = Field(
        default=None,
        max_length=2000,
    )
    steps: list[ProcurementApprovalStepCreate] = Field(
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_step_numbers(
        self,
    ) -> "ProcurementApprovalRequestCreate":
        numbers = [
            step.step_number
            for step in self.steps
        ]

        if len(numbers) != len(set(numbers)):
            raise ValueError(
                "approval step numbers must be unique"
            )

        if sorted(numbers) != list(
            range(1, len(numbers) + 1)
        ):
            raise ValueError(
                "approval step numbers must be contiguous "
                "starting at 1"
            )

        return self


class ProcurementApprovalStepDecision(ApprovalSchemaBase):
    decided_by: UUID
    comments: str | None = Field(
        default=None,
        max_length=2000,
    )


class ProcurementApprovalRequestCancel(ApprovalSchemaBase):
    comments: str | None = Field(
        default=None,
        max_length=2000,
    )


class ProcurementApprovalStepRead(ApprovalSchemaBase):
    id: UUID
    tenant_id: UUID
    approval_request_id: UUID
    step_number: int
    status: ApprovalStepStatus

    approver_id: UUID | None = None
    decided_by: UUID | None = None
    decided_at: datetime | None = None
    comments: str | None = None

    created_at: datetime
    updated_at: datetime


class ProcurementApprovalRequestRead(ApprovalSchemaBase):
    id: UUID
    tenant_id: UUID

    object_type: ApprovalObjectType
    object_id: UUID

    status: ApprovalRequestStatus

    requested_by: UUID
    requested_at: datetime
    completed_at: datetime | None = None

    current_step: int
    total_steps: int

    comments: str | None = None

    created_at: datetime
    updated_at: datetime

    steps: list[ProcurementApprovalStepRead] = Field(
        default_factory=list,
    )

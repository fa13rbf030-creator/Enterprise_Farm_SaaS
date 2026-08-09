from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from procurement_service.core.enums import (
    ApprovalRequestStatus,
    ApprovalStepStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    ProcurementApprovalStep,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepDecision,
)


class ApprovalWorkflowError(ValueError):
    """Base error for approval workflow rule violations."""


class ApprovalRequestTerminalError(ApprovalWorkflowError):
    """Raised when a terminal approval request is modified."""


class ApprovalStepOrderError(ApprovalWorkflowError):
    """Raised when a step is decided out of sequence."""


class ApprovalStepDecisionError(ApprovalWorkflowError):
    """Raised when a step cannot accept another decision."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalWorkflowService:
    @staticmethod
    def create_request(
        *,
        tenant_id: UUID,
        payload: ProcurementApprovalRequestCreate,
    ) -> ProcurementApprovalRequest:
        now = utc_now()

        request = ProcurementApprovalRequest(
            id=uuid4(),
            tenant_id=tenant_id,
            object_type=payload.object_type,
            object_id=payload.object_id,
            status=ApprovalRequestStatus.PENDING,
            requested_by=payload.requested_by,
            requested_at=now,
            completed_at=None,
            current_step=1,
            total_steps=len(payload.steps),
            comments=payload.comments,
            created_at=now,
            updated_at=now,
        )

        request.steps = [
            ProcurementApprovalStep(
                id=uuid4(),
                tenant_id=tenant_id,
                approval_request_id=request.id,
                step_number=step.step_number,
                status=ApprovalStepStatus.PENDING,
                approver_id=step.approver_id,
                decided_by=None,
                decided_at=None,
                comments=None,
                created_at=now,
                updated_at=now,
            )
            for step in payload.steps
        ]

        return request

    @staticmethod
    def approve_step(
        *,
        request: ProcurementApprovalRequest,
        step_number: int,
        decision: ProcurementApprovalStepDecision,
    ) -> ProcurementApprovalRequest:
        ApprovalWorkflowService._ensure_request_active(
            request
        )

        step = ApprovalWorkflowService._get_step(
            request,
            step_number,
        )

        ApprovalWorkflowService._ensure_current_step(
            request,
            step,
        )

        ApprovalWorkflowService._ensure_step_pending(
            step
        )

        now = utc_now()

        step.status = ApprovalStepStatus.APPROVED
        step.decided_by = decision.decided_by
        step.decided_at = now
        step.comments = decision.comments
        step.updated_at = now

        if step.step_number == request.total_steps:
            request.status = ApprovalRequestStatus.APPROVED
            request.completed_at = now
        else:
            request.current_step += 1
            request.status = ApprovalRequestStatus.IN_PROGRESS

        request.updated_at = now

        return request

    @staticmethod
    def reject_step(
        *,
        request: ProcurementApprovalRequest,
        step_number: int,
        decision: ProcurementApprovalStepDecision,
    ) -> ProcurementApprovalRequest:
        ApprovalWorkflowService._ensure_request_active(
            request
        )

        step = ApprovalWorkflowService._get_step(
            request,
            step_number,
        )

        ApprovalWorkflowService._ensure_current_step(
            request,
            step,
        )

        ApprovalWorkflowService._ensure_step_pending(
            step
        )

        now = utc_now()

        step.status = ApprovalStepStatus.REJECTED
        step.decided_by = decision.decided_by
        step.decided_at = now
        step.comments = decision.comments
        step.updated_at = now

        for future_step in request.steps:
            if (
                future_step.step_number > step.step_number
                and future_step.status
                == ApprovalStepStatus.PENDING
            ):
                future_step.status = ApprovalStepStatus.SKIPPED
                future_step.updated_at = now

        request.status = ApprovalRequestStatus.REJECTED
        request.completed_at = now
        request.updated_at = now

        return request

    @staticmethod
    def cancel_request(
        *,
        request: ProcurementApprovalRequest,
        comments: str | None = None,
    ) -> ProcurementApprovalRequest:
        ApprovalWorkflowService._ensure_request_active(
            request
        )

        now = utc_now()

        for step in request.steps:
            if step.status == ApprovalStepStatus.PENDING:
                step.status = ApprovalStepStatus.SKIPPED
                step.updated_at = now

        request.status = ApprovalRequestStatus.CANCELLED
        request.completed_at = now

        if comments is not None:
            request.comments = comments

        request.updated_at = now

        return request

    @staticmethod
    def _ensure_request_active(
        request: ProcurementApprovalRequest,
    ) -> None:
        terminal = {
            ApprovalRequestStatus.APPROVED,
            ApprovalRequestStatus.REJECTED,
            ApprovalRequestStatus.CANCELLED,
        }

        if request.status in terminal:
            raise ApprovalRequestTerminalError(
                "approval request is already terminal"
            )

    @staticmethod
    def _get_step(
        request: ProcurementApprovalRequest,
        step_number: int,
    ) -> ProcurementApprovalStep:
        for step in request.steps:
            if step.step_number == step_number:
                return step

        raise ApprovalStepOrderError(
            f"approval step {step_number} does not exist"
        )

    @staticmethod
    def _ensure_current_step(
        request: ProcurementApprovalRequest,
        step: ProcurementApprovalStep,
    ) -> None:
        if step.step_number != request.current_step:
            raise ApprovalStepOrderError(
                "approval decisions must follow step order"
            )

    @staticmethod
    def _ensure_step_pending(
        step: ProcurementApprovalStep,
    ) -> None:
        if step.status != ApprovalStepStatus.PENDING:
            raise ApprovalStepDecisionError(
                "approval step already has a decision"
            )

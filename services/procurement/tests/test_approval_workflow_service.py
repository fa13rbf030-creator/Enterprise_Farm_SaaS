from uuid import uuid4

import pytest

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    ApprovalStepStatus,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.approval import (
    ApprovalRequestTerminalError,
    ApprovalStepDecisionError,
    ApprovalStepOrderError,
    ApprovalWorkflowService,
)


def build_request(step_count: int = 2):
    return ApprovalWorkflowService.create_request(
        tenant_id=uuid4(),
        payload=ProcurementApprovalRequestCreate(
            object_type=ApprovalObjectType.PURCHASE_ORDER,
            object_id=uuid4(),
            requested_by=uuid4(),
            comments="approval requested",
            steps=[
                ProcurementApprovalStepCreate(
                    step_number=number,
                    approver_id=uuid4(),
                )
                for number in range(
                    1,
                    step_count + 1,
                )
            ],
        ),
    )


def decision():
    return ProcurementApprovalStepDecision(
        decided_by=uuid4(),
        comments="decision recorded",
    )


def test_create_request_builds_ordered_steps():
    request = build_request(2)

    assert request.status == ApprovalRequestStatus.PENDING
    assert request.current_step == 1
    assert request.total_steps == 2

    assert [
        step.step_number
        for step in request.steps
    ] == [1, 2]

    assert all(
        step.status == ApprovalStepStatus.PENDING
        for step in request.steps
    )


def test_create_request_propagates_tenant():
    request = build_request(2)

    assert all(
        step.tenant_id == request.tenant_id
        for step in request.steps
    )


def test_approve_first_step_advances_request():
    request = build_request(2)

    ApprovalWorkflowService.approve_step(
        request=request,
        step_number=1,
        decision=decision(),
    )

    assert (
        request.steps[0].status
        == ApprovalStepStatus.APPROVED
    )
    assert request.current_step == 2
    assert (
        request.status
        == ApprovalRequestStatus.IN_PROGRESS
    )
    assert request.completed_at is None


def test_final_approval_completes_request():
    request = build_request(2)

    ApprovalWorkflowService.approve_step(
        request=request,
        step_number=1,
        decision=decision(),
    )

    ApprovalWorkflowService.approve_step(
        request=request,
        step_number=2,
        decision=decision(),
    )

    assert request.status == ApprovalRequestStatus.APPROVED
    assert request.completed_at is not None

    assert all(
        step.status == ApprovalStepStatus.APPROVED
        for step in request.steps
    )


def test_out_of_order_approval_is_rejected():
    request = build_request(2)

    with pytest.raises(ApprovalStepOrderError):
        ApprovalWorkflowService.approve_step(
            request=request,
            step_number=2,
            decision=decision(),
        )


def test_reject_current_step_rejects_request():
    request = build_request(2)

    ApprovalWorkflowService.reject_step(
        request=request,
        step_number=1,
        decision=decision(),
    )

    assert request.status == ApprovalRequestStatus.REJECTED
    assert request.completed_at is not None

    assert (
        request.steps[0].status
        == ApprovalStepStatus.REJECTED
    )

    assert (
        request.steps[1].status
        == ApprovalStepStatus.SKIPPED
    )


def test_cancel_skips_pending_steps():
    request = build_request(3)

    ApprovalWorkflowService.cancel_request(
        request=request,
        comments="cancelled by requester",
    )

    assert (
        request.status
        == ApprovalRequestStatus.CANCELLED
    )

    assert request.completed_at is not None

    assert all(
        step.status == ApprovalStepStatus.SKIPPED
        for step in request.steps
    )

    assert request.comments == "cancelled by requester"


def test_terminal_request_cannot_be_decided_again():
    request = build_request(1)

    ApprovalWorkflowService.approve_step(
        request=request,
        step_number=1,
        decision=decision(),
    )

    with pytest.raises(
        ApprovalRequestTerminalError
    ):
        ApprovalWorkflowService.approve_step(
            request=request,
            step_number=1,
            decision=decision(),
        )


def test_terminal_request_cannot_be_cancelled():
    request = build_request(1)

    ApprovalWorkflowService.reject_step(
        request=request,
        step_number=1,
        decision=decision(),
    )

    with pytest.raises(
        ApprovalRequestTerminalError
    ):
        ApprovalWorkflowService.cancel_request(
            request=request,
        )


def test_unknown_step_is_rejected():
    request = build_request(2)

    with pytest.raises(ApprovalStepOrderError):
        ApprovalWorkflowService.approve_step(
            request=request,
            step_number=99,
            decision=decision(),
        )


def test_duplicate_step_decision_is_rejected():
    request = build_request(2)

    ApprovalWorkflowService.approve_step(
        request=request,
        step_number=1,
        decision=decision(),
    )

    request.current_step = 1

    with pytest.raises(
        ApprovalStepDecisionError
    ):
        ApprovalWorkflowService.approve_step(
            request=request,
            step_number=1,
            decision=decision(),
        )


def test_decision_metadata_is_recorded():
    request = build_request(1)
    actor = uuid4()

    ApprovalWorkflowService.approve_step(
        request=request,
        step_number=1,
        decision=ProcurementApprovalStepDecision(
            decided_by=actor,
            comments="approved by controller",
        ),
    )

    step = request.steps[0]

    assert step.decided_by == actor
    assert step.decided_at is not None
    assert step.comments == "approved by controller"

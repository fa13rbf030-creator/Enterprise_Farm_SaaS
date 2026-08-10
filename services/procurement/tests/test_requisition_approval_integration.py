from datetime import UTC, datetime
from uuid import uuid4

import pytest

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    RequisitionStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    PurchaseRequisition,
)
from procurement_service.services.requisition_approval import (
    ApprovalNotTerminalError,
    ApprovalObjectMismatchError,
    InvalidRequisitionTransitionError,
    RequisitionApprovalIntegrationService,
)


def make_requisition(
    *,
    status: RequisitionStatus = RequisitionStatus.DRAFT,
) -> PurchaseRequisition:
    return PurchaseRequisition(
        id=uuid4(),
        tenant_id=uuid4(),
        requisition_number=f"PR-{uuid4()}",
        requester_id=uuid4(),
        purpose="approval integration test",
        status=status,
    )


def make_approval(
    requisition: PurchaseRequisition,
    *,
    status: ApprovalRequestStatus,
) -> ProcurementApprovalRequest:
    now = datetime.now(UTC)

    return ProcurementApprovalRequest(
        id=uuid4(),
        tenant_id=requisition.tenant_id,
        object_type=ApprovalObjectType.PURCHASE_REQUISITION,
        object_id=requisition.id,
        status=status,
        requested_by=requisition.requester_id,
        requested_at=now,
        completed_at=(
            now
            if status
            in {
                ApprovalRequestStatus.APPROVED,
                ApprovalRequestStatus.REJECTED,
                ApprovalRequestStatus.CANCELLED,
            }
            else None
        ),
        current_step=1,
        total_steps=1,
        created_at=now,
        updated_at=now,
    )


def test_submit_moves_draft_to_submitted():
    requisition = make_requisition()

    result = (
        RequisitionApprovalIntegrationService.submit(
            requisition=requisition
        )
    )

    assert result is requisition
    assert requisition.status == RequisitionStatus.SUBMITTED
    assert requisition.submitted_at is not None


def test_submit_rejects_non_draft():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    with pytest.raises(
        InvalidRequisitionTransitionError
    ):
        RequisitionApprovalIntegrationService.submit(
            requisition=requisition
        )


def test_approved_request_synchronizes_requisition():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    approval = make_approval(
        requisition,
        status=ApprovalRequestStatus.APPROVED,
    )

    approver_id = uuid4()

    RequisitionApprovalIntegrationService.synchronize_terminal_approval(
        requisition=requisition,
        approval_request=approval,
        decided_by=approver_id,
    )

    assert requisition.status == RequisitionStatus.APPROVED
    assert requisition.approved_by == approver_id
    assert requisition.approved_at == approval.completed_at
    assert requisition.rejection_reason is None


def test_rejected_request_synchronizes_requisition():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    approval = make_approval(
        requisition,
        status=ApprovalRequestStatus.REJECTED,
    )

    RequisitionApprovalIntegrationService.synchronize_terminal_approval(
        requisition=requisition,
        approval_request=approval,
        rejection_reason="Budget rejected",
    )

    assert requisition.status == RequisitionStatus.REJECTED
    assert requisition.approved_by is None
    assert requisition.approved_at is None
    assert requisition.rejection_reason == "Budget rejected"


def test_cancelled_request_synchronizes_requisition():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    approval = make_approval(
        requisition,
        status=ApprovalRequestStatus.CANCELLED,
    )

    RequisitionApprovalIntegrationService.synchronize_terminal_approval(
        requisition=requisition,
        approval_request=approval,
    )

    assert requisition.status == RequisitionStatus.CANCELLED


def test_non_terminal_approval_cannot_synchronize():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    approval = make_approval(
        requisition,
        status=ApprovalRequestStatus.IN_PROGRESS,
    )

    with pytest.raises(ApprovalNotTerminalError):
        RequisitionApprovalIntegrationService.synchronize_terminal_approval(
            requisition=requisition,
            approval_request=approval,
        )


def test_wrong_object_type_is_rejected():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    approval = make_approval(
        requisition,
        status=ApprovalRequestStatus.APPROVED,
    )

    approval.object_type = ApprovalObjectType.PURCHASE_ORDER

    with pytest.raises(ApprovalObjectMismatchError):
        RequisitionApprovalIntegrationService.synchronize_terminal_approval(
            requisition=requisition,
            approval_request=approval,
        )


def test_wrong_object_id_is_rejected():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    approval = make_approval(
        requisition,
        status=ApprovalRequestStatus.APPROVED,
    )

    approval.object_id = uuid4()

    with pytest.raises(ApprovalObjectMismatchError):
        RequisitionApprovalIntegrationService.synchronize_terminal_approval(
            requisition=requisition,
            approval_request=approval,
        )


def test_wrong_tenant_is_rejected():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    approval = make_approval(
        requisition,
        status=ApprovalRequestStatus.APPROVED,
    )

    approval.tenant_id = uuid4()

    with pytest.raises(ApprovalObjectMismatchError):
        RequisitionApprovalIntegrationService.synchronize_terminal_approval(
            requisition=requisition,
            approval_request=approval,
        )


def test_non_submitted_requisition_cannot_receive_outcome():
    requisition = make_requisition(
        status=RequisitionStatus.DRAFT
    )

    approval = make_approval(
        requisition,
        status=ApprovalRequestStatus.APPROVED,
    )

    with pytest.raises(
        InvalidRequisitionTransitionError
    ):
        RequisitionApprovalIntegrationService.synchronize_terminal_approval(
            requisition=requisition,
            approval_request=approval,
        )

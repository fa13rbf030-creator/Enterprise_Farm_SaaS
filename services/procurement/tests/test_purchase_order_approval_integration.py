from datetime import UTC, datetime
from uuid import uuid4

import pytest

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    PurchaseOrderStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    PurchaseOrder,
)
from procurement_service.services.purchase_order_approval import (
    InvalidPurchaseOrderTransitionError,
    PurchaseOrderApprovalIntegrationService,
    PurchaseOrderApprovalMismatchError,
)


def purchase_order(
    *,
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT,
) -> PurchaseOrder:
    return PurchaseOrder(
        id=uuid4(),
        tenant_id=uuid4(),
        po_number="PO-R4B-001",
        supplier_id=uuid4(),
        order_date=datetime.now(UTC).date(),
        requested_by=uuid4(),
        status=status,
    )


def approval_for(
    po: PurchaseOrder,
    *,
    status: ApprovalRequestStatus,
) -> ProcurementApprovalRequest:
    return ProcurementApprovalRequest(
        id=uuid4(),
        tenant_id=po.tenant_id,
        object_type=ApprovalObjectType.PURCHASE_ORDER,
        object_id=po.id,
        status=status,
        requested_by=uuid4(),
        current_step=1,
        completed_at=(
            datetime.now(UTC)
            if status
            in {
                ApprovalRequestStatus.APPROVED,
                ApprovalRequestStatus.REJECTED,
                ApprovalRequestStatus.CANCELLED,
            }
            else None
        ),
    )


def test_submit_moves_draft_to_pending_approval():
    po = purchase_order()

    PurchaseOrderApprovalIntegrationService.submit(po)

    assert po.status == PurchaseOrderStatus.PENDING_APPROVAL
    assert po.approved_by is None
    assert po.approved_at is None


def test_non_draft_purchase_order_cannot_submit():
    po = purchase_order(
        status=PurchaseOrderStatus.APPROVED
    )

    with pytest.raises(
        InvalidPurchaseOrderTransitionError
    ):
        PurchaseOrderApprovalIntegrationService.submit(po)


def test_approved_request_synchronizes_purchase_order():
    po = purchase_order(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    approval = approval_for(
        po,
        status=ApprovalRequestStatus.APPROVED,
    )
    approver_id = uuid4()

    PurchaseOrderApprovalIntegrationService.synchronize_outcome(
        po,
        approval,
        decided_by=approver_id,
    )

    assert po.status == PurchaseOrderStatus.APPROVED
    assert po.approved_by == approver_id
    assert po.approved_at == approval.completed_at


def test_rejected_request_returns_purchase_order_to_draft():
    po = purchase_order(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    approval = approval_for(
        po,
        status=ApprovalRequestStatus.REJECTED,
    )

    PurchaseOrderApprovalIntegrationService.synchronize_outcome(
        po,
        approval,
        decided_by=uuid4(),
        rejection_reason="Budget rejected",
    )

    assert po.status == PurchaseOrderStatus.DRAFT
    assert po.approved_by is None
    assert po.approved_at is None


def test_cancelled_approval_returns_purchase_order_to_draft():
    po = purchase_order(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    approval = approval_for(
        po,
        status=ApprovalRequestStatus.CANCELLED,
    )

    PurchaseOrderApprovalIntegrationService.synchronize_outcome(
        po,
        approval,
    )

    assert po.status == PurchaseOrderStatus.DRAFT
    assert po.cancelled_at is None


def test_wrong_object_type_is_rejected():
    po = purchase_order(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    approval = approval_for(
        po,
        status=ApprovalRequestStatus.APPROVED,
    )
    approval.object_type = (
        ApprovalObjectType.PURCHASE_REQUISITION
    )

    with pytest.raises(
        PurchaseOrderApprovalMismatchError
    ):
        PurchaseOrderApprovalIntegrationService.synchronize_outcome(
            po,
            approval,
        )


def test_wrong_object_id_is_rejected():
    po = purchase_order(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    approval = approval_for(
        po,
        status=ApprovalRequestStatus.APPROVED,
    )
    approval.object_id = uuid4()

    with pytest.raises(
        PurchaseOrderApprovalMismatchError
    ):
        PurchaseOrderApprovalIntegrationService.synchronize_outcome(
            po,
            approval,
        )


def test_wrong_tenant_is_rejected():
    po = purchase_order(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    approval = approval_for(
        po,
        status=ApprovalRequestStatus.APPROVED,
    )
    approval.tenant_id = uuid4()

    with pytest.raises(
        PurchaseOrderApprovalMismatchError
    ):
        PurchaseOrderApprovalIntegrationService.synchronize_outcome(
            po,
            approval,
        )


def test_pending_approval_cannot_be_synchronized_as_outcome():
    po = purchase_order(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    approval = approval_for(
        po,
        status=ApprovalRequestStatus.PENDING,
    )

    with pytest.raises(
        InvalidPurchaseOrderTransitionError
    ):
        PurchaseOrderApprovalIntegrationService.synchronize_outcome(
            po,
            approval,
        )

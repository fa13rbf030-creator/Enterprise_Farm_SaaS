from datetime import UTC, datetime
from uuid import UUID

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    PurchaseOrderStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    PurchaseOrder,
)


class PurchaseOrderApprovalIntegrationError(ValueError):
    """Base purchase-order approval integration error."""


class InvalidPurchaseOrderTransitionError(
    PurchaseOrderApprovalIntegrationError
):
    """Raised when a purchase order cannot accept a transition."""


class PurchaseOrderApprovalMismatchError(
    PurchaseOrderApprovalIntegrationError
):
    """Raised when an approval request targets another object."""


def utc_now() -> datetime:
    return datetime.now(UTC)


class PurchaseOrderApprovalIntegrationService:
    @staticmethod
    def submit(
        purchase_order: PurchaseOrder,
    ) -> PurchaseOrder:
        if purchase_order.status != PurchaseOrderStatus.DRAFT:
            raise InvalidPurchaseOrderTransitionError(
                "only draft purchase orders can be submitted"
            )

        purchase_order.status = (
            PurchaseOrderStatus.PENDING_APPROVAL
        )
        purchase_order.approved_by = None
        purchase_order.approved_at = None

        return purchase_order

    @staticmethod
    def synchronize_outcome(
        purchase_order: PurchaseOrder,
        approval: ProcurementApprovalRequest,
        *,
        decided_by: UUID | None = None,
        rejection_reason: str | None = None,
    ) -> PurchaseOrder:
        if (
            approval.object_type
            != ApprovalObjectType.PURCHASE_ORDER
        ):
            raise PurchaseOrderApprovalMismatchError(
                "approval request does not target a purchase order"
            )

        if approval.object_id != purchase_order.id:
            raise PurchaseOrderApprovalMismatchError(
                "approval request targets another purchase order"
            )

        if approval.tenant_id != purchase_order.tenant_id:
            raise PurchaseOrderApprovalMismatchError(
                "approval request belongs to another tenant"
            )

        if (
            purchase_order.status
            != PurchaseOrderStatus.PENDING_APPROVAL
        ):
            raise InvalidPurchaseOrderTransitionError(
                "only pending-approval purchase orders can "
                "receive an approval outcome"
            )

        if approval.status == ApprovalRequestStatus.APPROVED:
            purchase_order.status = PurchaseOrderStatus.APPROVED
            purchase_order.approved_by = decided_by
            purchase_order.approved_at = (
                approval.completed_at or utc_now()
            )
            return purchase_order

        if approval.status == ApprovalRequestStatus.REJECTED:
            # PurchaseOrderStatus intentionally has no REJECTED
            # state. A rejected approval returns the PO to DRAFT
            # so it can be corrected and resubmitted.
            purchase_order.status = PurchaseOrderStatus.DRAFT
            purchase_order.approved_by = None
            purchase_order.approved_at = None
            return purchase_order

        if approval.status == ApprovalRequestStatus.CANCELLED:
            # Cancelling the approval workflow does not cancel the
            # commercial purchase order itself. Return it to DRAFT.
            purchase_order.status = PurchaseOrderStatus.DRAFT
            purchase_order.approved_by = None
            purchase_order.approved_at = None
            return purchase_order

        raise InvalidPurchaseOrderTransitionError(
            "approval request has not reached a terminal state"
        )

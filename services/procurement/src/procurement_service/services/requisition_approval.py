from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    RequisitionStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    PurchaseRequisition,
)


class RequisitionApprovalIntegrationError(ValueError):
    """Base requisition/approval integration error."""


class InvalidRequisitionTransitionError(
    RequisitionApprovalIntegrationError
):
    """Raised when requisition state cannot accept a transition."""


class ApprovalObjectMismatchError(
    RequisitionApprovalIntegrationError
):
    """Raised when an approval targets another business object."""


class ApprovalNotTerminalError(
    RequisitionApprovalIntegrationError
):
    """Raised when synchronization is attempted too early."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RequisitionApprovalIntegrationService:
    @staticmethod
    def submit(
        *,
        requisition: PurchaseRequisition,
    ) -> PurchaseRequisition:
        if requisition.status != RequisitionStatus.DRAFT:
            raise InvalidRequisitionTransitionError(
                "only draft requisitions can be submitted"
            )

        requisition.status = RequisitionStatus.SUBMITTED
        requisition.submitted_at = utc_now()
        requisition.approved_by = None
        requisition.approved_at = None
        requisition.rejection_reason = None

        return requisition

    @staticmethod
    def validate_approval_target(
        *,
        requisition: PurchaseRequisition,
        approval_request: ProcurementApprovalRequest,
    ) -> None:
        if (
            approval_request.tenant_id
            != requisition.tenant_id
        ):
            raise ApprovalObjectMismatchError(
                "approval request tenant does not match requisition"
            )

        if (
            approval_request.object_type
            != ApprovalObjectType.PURCHASE_REQUISITION
        ):
            raise ApprovalObjectMismatchError(
                "approval request is not for a purchase requisition"
            )

        if approval_request.object_id != requisition.id:
            raise ApprovalObjectMismatchError(
                "approval request does not target this requisition"
            )

    @staticmethod
    def synchronize_terminal_approval(
        *,
        requisition: PurchaseRequisition,
        approval_request: ProcurementApprovalRequest,
        decided_by: UUID | None = None,
        rejection_reason: str | None = None,
    ) -> PurchaseRequisition:
        RequisitionApprovalIntegrationService.validate_approval_target(
            requisition=requisition,
            approval_request=approval_request,
        )

        if requisition.status != RequisitionStatus.SUBMITTED:
            raise InvalidRequisitionTransitionError(
                "only submitted requisitions can receive "
                "an approval outcome"
            )

        now = approval_request.completed_at or utc_now()

        if (
            approval_request.status
            == ApprovalRequestStatus.APPROVED
        ):
            requisition.status = RequisitionStatus.APPROVED
            requisition.approved_by = decided_by
            requisition.approved_at = now
            requisition.rejection_reason = None

            return requisition

        if (
            approval_request.status
            == ApprovalRequestStatus.REJECTED
        ):
            requisition.status = RequisitionStatus.REJECTED
            requisition.approved_by = None
            requisition.approved_at = None
            requisition.rejection_reason = rejection_reason

            return requisition

        if (
            approval_request.status
            == ApprovalRequestStatus.CANCELLED
        ):
            requisition.status = RequisitionStatus.CANCELLED
            requisition.approved_by = None
            requisition.approved_at = None

            return requisition

        raise ApprovalNotTerminalError(
            "approval request has not reached a terminal state"
        )

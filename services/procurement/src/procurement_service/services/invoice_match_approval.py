from datetime import UTC, datetime
from uuid import UUID

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    InvoiceMatchStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    SupplierInvoiceMatch,
)


class InvoiceMatchApprovalIntegrationError(ValueError):
    """Base invoice-match approval integration error."""


class InvalidInvoiceMatchTransitionError(
    InvoiceMatchApprovalIntegrationError
):
    """Raised when an invoice match cannot accept a transition."""


class InvoiceMatchApprovalMismatchError(
    InvoiceMatchApprovalIntegrationError
):
    """Raised when approval does not belong to the invoice match."""


def utc_now() -> datetime:
    return datetime.now(UTC)


class InvoiceMatchApprovalIntegrationService:
    @staticmethod
    def submit(
        invoice_match: SupplierInvoiceMatch,
    ) -> SupplierInvoiceMatch:
        if invoice_match.status not in {
            InvoiceMatchStatus.MATCHED,
            InvoiceMatchStatus.WITHIN_TOLERANCE,
            InvoiceMatchStatus.EXCEPTION,
            InvoiceMatchStatus.DISPUTED,
            InvoiceMatchStatus.REJECTED,
        }:
            raise InvalidInvoiceMatchTransitionError(
                "invoice match is not eligible for approval submission"
            )

        invoice_match.approved_by = None
        invoice_match.approved_at = None

        return invoice_match

    @staticmethod
    def synchronize_outcome(
        *,
        invoice_match: SupplierInvoiceMatch,
        approval: ProcurementApprovalRequest,
        decided_by: UUID,
        rejection_reason: str | None = None,
    ) -> SupplierInvoiceMatch:
        if approval.object_type != ApprovalObjectType.INVOICE_MATCH:
            raise InvoiceMatchApprovalMismatchError(
                "approval object type is not INVOICE_MATCH"
            )

        if approval.object_id != invoice_match.id:
            raise InvoiceMatchApprovalMismatchError(
                "approval object id does not match invoice match"
            )

        if approval.tenant_id != invoice_match.tenant_id:
            raise InvoiceMatchApprovalMismatchError(
                "approval tenant does not match invoice match"
            )

        if approval.status == ApprovalRequestStatus.APPROVED:
            invoice_match.status = InvoiceMatchStatus.APPROVED
            invoice_match.approved_by = decided_by
            invoice_match.approved_at = (
                approval.completed_at or utc_now()
            )
            invoice_match.dispute_reason = None

            return invoice_match

        if approval.status == ApprovalRequestStatus.REJECTED:
            invoice_match.status = InvoiceMatchStatus.REJECTED
            invoice_match.approved_by = None
            invoice_match.approved_at = None

            if rejection_reason:
                invoice_match.dispute_reason = rejection_reason

            return invoice_match

        raise InvalidInvoiceMatchTransitionError(
            "approval request is not terminal"
        )

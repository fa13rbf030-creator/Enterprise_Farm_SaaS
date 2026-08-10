from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    InvoiceMatchStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    SupplierInvoiceMatch,
)
from procurement_service.services.invoice_match_approval import (
    InvalidInvoiceMatchTransitionError,
    InvoiceMatchApprovalIntegrationService,
    InvoiceMatchApprovalMismatchError,
)


def make_match(
    *,
    status: InvoiceMatchStatus = InvoiceMatchStatus.MATCHED,
) -> SupplierInvoiceMatch:
    return SupplierInvoiceMatch(
        id=uuid4(),
        tenant_id=uuid4(),
        supplier_id=uuid4(),
        purchase_order_id=uuid4(),
        supplier_invoice_number="INV-R5B-001",
        supplier_invoice_date=date.today(),
        currency_code="PKR",
        invoice_subtotal=Decimal("100"),
        invoice_tax_amount=Decimal("0"),
        invoice_total=Decimal("100"),
        quantity_tolerance_percent=Decimal("0"),
        price_tolerance_percent=Decimal("0"),
        tax_tolerance_percent=Decimal("0"),
        status=status,
    )


def make_approval(
    invoice_match: SupplierInvoiceMatch,
    *,
    status: ApprovalRequestStatus,
) -> ProcurementApprovalRequest:
    return ProcurementApprovalRequest(
        id=uuid4(),
        tenant_id=invoice_match.tenant_id,
        object_type=ApprovalObjectType.INVOICE_MATCH,
        object_id=invoice_match.id,
        status=status,
        requested_by=uuid4(),
        current_step=1,
        completed_at=(
            datetime.now(UTC)
            if status
            in {
                ApprovalRequestStatus.APPROVED,
                ApprovalRequestStatus.REJECTED,
            }
            else None
        ),
    )


@pytest.mark.parametrize(
    "status",
    [
        InvoiceMatchStatus.MATCHED,
        InvoiceMatchStatus.WITHIN_TOLERANCE,
        InvoiceMatchStatus.EXCEPTION,
        InvoiceMatchStatus.DISPUTED,
        InvoiceMatchStatus.REJECTED,
    ],
)
def test_eligible_match_can_be_submitted(status):
    match = make_match(status=status)
    match.approved_by = uuid4()
    match.approved_at = datetime.now(UTC)

    result = InvoiceMatchApprovalIntegrationService.submit(match)

    assert result is match
    assert match.approved_by is None
    assert match.approved_at is None


@pytest.mark.parametrize(
    "status",
    [
        InvoiceMatchStatus.PENDING,
        InvoiceMatchStatus.APPROVED,
        InvoiceMatchStatus.HANDED_OFF,
    ],
)
def test_ineligible_match_cannot_be_submitted(status):
    match = make_match(status=status)

    with pytest.raises(InvalidInvoiceMatchTransitionError):
        InvoiceMatchApprovalIntegrationService.submit(match)


def test_approved_request_synchronizes_invoice_match():
    match = make_match()
    approval = make_approval(
        match,
        status=ApprovalRequestStatus.APPROVED,
    )
    approver_id = uuid4()

    result = (
        InvoiceMatchApprovalIntegrationService.synchronize_outcome(
            invoice_match=match,
            approval=approval,
            decided_by=approver_id,
        )
    )

    assert result is match
    assert match.status == InvoiceMatchStatus.APPROVED
    assert match.approved_by == approver_id
    assert match.approved_at == approval.completed_at
    assert match.dispute_reason is None


def test_rejected_request_synchronizes_invoice_match():
    match = make_match()
    approval = make_approval(
        match,
        status=ApprovalRequestStatus.REJECTED,
    )

    InvoiceMatchApprovalIntegrationService.synchronize_outcome(
        invoice_match=match,
        approval=approval,
        decided_by=uuid4(),
        rejection_reason="Price variance rejected",
    )

    assert match.status == InvoiceMatchStatus.REJECTED
    assert match.approved_by is None
    assert match.approved_at is None
    assert match.dispute_reason == "Price variance rejected"


def test_wrong_object_type_is_rejected():
    match = make_match()
    approval = make_approval(
        match,
        status=ApprovalRequestStatus.APPROVED,
    )
    approval.object_type = ApprovalObjectType.PURCHASE_ORDER

    with pytest.raises(InvoiceMatchApprovalMismatchError):
        InvoiceMatchApprovalIntegrationService.synchronize_outcome(
            invoice_match=match,
            approval=approval,
            decided_by=uuid4(),
        )


def test_wrong_object_id_is_rejected():
    match = make_match()
    approval = make_approval(
        match,
        status=ApprovalRequestStatus.APPROVED,
    )
    approval.object_id = uuid4()

    with pytest.raises(InvoiceMatchApprovalMismatchError):
        InvoiceMatchApprovalIntegrationService.synchronize_outcome(
            invoice_match=match,
            approval=approval,
            decided_by=uuid4(),
        )


def test_wrong_tenant_is_rejected():
    match = make_match()
    approval = make_approval(
        match,
        status=ApprovalRequestStatus.APPROVED,
    )
    approval.tenant_id = uuid4()

    with pytest.raises(InvoiceMatchApprovalMismatchError):
        InvoiceMatchApprovalIntegrationService.synchronize_outcome(
            invoice_match=match,
            approval=approval,
            decided_by=uuid4(),
        )


def test_pending_approval_cannot_be_synchronized():
    match = make_match()
    approval = make_approval(
        match,
        status=ApprovalRequestStatus.PENDING,
    )

    with pytest.raises(InvalidInvoiceMatchTransitionError):
        InvoiceMatchApprovalIntegrationService.synchronize_outcome(
            invoice_match=match,
            approval=approval,
            decided_by=uuid4(),
        )

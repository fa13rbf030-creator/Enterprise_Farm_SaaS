from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
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
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.invoice_match_approval_coordinator import (
    DuplicateInvoiceMatchApprovalError,
    InvoiceMatchApprovalCoordinator,
    InvoiceMatchApprovalCoordinatorError,
    InvoiceMatchApprovalNotFoundError,
    InvoiceMatchNotFoundError,
)


def make_match(
    *,
    tenant_id=None,
    status=InvoiceMatchStatus.MATCHED,
):
    tenant_id = tenant_id or uuid4()

    return SupplierInvoiceMatch(
        id=uuid4(),
        tenant_id=tenant_id,
        supplier_id=uuid4(),
        purchase_order_id=uuid4(),
        supplier_invoice_number=f"INV-{uuid4()}",
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


def make_payload(
    invoice_match,
    *,
    object_type=None,
    object_id=None,
):
    return ProcurementApprovalRequestCreate(
        object_type=(
            object_type or ApprovalObjectType.INVOICE_MATCH
        ),
        object_id=object_id or invoice_match.id,
        requested_by=uuid4(),
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
                approver_id=uuid4(),
            )
        ],
    )


def make_approval(
    invoice_match,
    *,
    status=ApprovalRequestStatus.PENDING,
):
    now = datetime.now(UTC)

    approval = ProcurementApprovalRequest(
        id=uuid4(),
        tenant_id=invoice_match.tenant_id,
        object_type=ApprovalObjectType.INVOICE_MATCH,
        object_id=invoice_match.id,
        status=status,
        requested_by=uuid4(),
        requested_at=now,
        current_step=1,
        total_steps=1,
        created_at=now,
        updated_at=now,
    )

    approval.steps = []

    return approval


def make_coordinator():
    coordinator = object.__new__(
        InvoiceMatchApprovalCoordinator
    )

    coordinator.session = AsyncMock()
    coordinator.invoice_matches = AsyncMock()
    coordinator.approvals = AsyncMock()

    return coordinator


@pytest.mark.asyncio
async def test_submit_coordinates_match_and_approval():
    invoice_match = make_match()
    coordinator = make_coordinator()

    coordinator.invoice_matches.get_by_id.return_value = (
        invoice_match
    )
    coordinator.approvals.get_by_object.return_value = None

    result_match, approval = (
        await coordinator.submit_for_approval(
            tenant_id=invoice_match.tenant_id,
            invoice_match_id=invoice_match.id,
            payload=make_payload(invoice_match),
        )
    )

    assert result_match is invoice_match
    assert approval.status == ApprovalRequestStatus.PENDING
    assert approval.object_id == invoice_match.id

    coordinator.approvals.add.assert_awaited_once_with(
        approval
    )


@pytest.mark.asyncio
async def test_submit_rejects_duplicate_approval():
    invoice_match = make_match()
    coordinator = make_coordinator()

    coordinator.invoice_matches.get_by_id.return_value = (
        invoice_match
    )
    coordinator.approvals.get_by_object.return_value = (
        make_approval(invoice_match)
    )

    with pytest.raises(
        DuplicateInvoiceMatchApprovalError
    ):
        await coordinator.submit_for_approval(
            tenant_id=invoice_match.tenant_id,
            invoice_match_id=invoice_match.id,
            payload=make_payload(invoice_match),
        )


@pytest.mark.asyncio
async def test_submit_rejects_missing_match():
    invoice_match = make_match()
    coordinator = make_coordinator()

    coordinator.invoice_matches.get_by_id.return_value = None

    with pytest.raises(InvoiceMatchNotFoundError):
        await coordinator.submit_for_approval(
            tenant_id=invoice_match.tenant_id,
            invoice_match_id=invoice_match.id,
            payload=make_payload(invoice_match),
        )


@pytest.mark.asyncio
async def test_submit_rejects_wrong_object_type():
    invoice_match = make_match()
    coordinator = make_coordinator()

    with pytest.raises(
        InvoiceMatchApprovalCoordinatorError
    ):
        await coordinator.submit_for_approval(
            tenant_id=invoice_match.tenant_id,
            invoice_match_id=invoice_match.id,
            payload=make_payload(
                invoice_match,
                object_type=ApprovalObjectType.PURCHASE_ORDER,
            ),
        )

    coordinator.invoice_matches.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_submit_rejects_wrong_object_id():
    invoice_match = make_match()
    coordinator = make_coordinator()

    with pytest.raises(
        InvoiceMatchApprovalCoordinatorError
    ):
        await coordinator.submit_for_approval(
            tenant_id=invoice_match.tenant_id,
            invoice_match_id=invoice_match.id,
            payload=make_payload(
                invoice_match,
                object_id=uuid4(),
            ),
        )


@pytest.mark.asyncio
async def test_decision_rejects_missing_approval():
    invoice_match = make_match()
    coordinator = make_coordinator()

    coordinator.invoice_matches.get_by_id.return_value = (
        invoice_match
    )
    coordinator.approvals.get_by_object.return_value = None

    with pytest.raises(
        InvoiceMatchApprovalNotFoundError
    ):
        await coordinator.approve_step(
            tenant_id=invoice_match.tenant_id,
            invoice_match_id=invoice_match.id,
            step_number=1,
            decision=ProcurementApprovalStepDecision(
                decided_by=uuid4(),
            ),
        )


@pytest.mark.asyncio
async def test_load_for_decision_uses_tenant_scoped_locks():
    invoice_match = make_match()
    approval = make_approval(invoice_match)
    coordinator = make_coordinator()

    coordinator.invoice_matches.get_by_id.return_value = (
        invoice_match
    )
    coordinator.approvals.get_by_object.return_value = approval

    loaded_match, loaded_approval = (
        await coordinator._load_for_decision(
            tenant_id=invoice_match.tenant_id,
            invoice_match_id=invoice_match.id,
        )
    )

    assert loaded_match is invoice_match
    assert loaded_approval is approval

    coordinator.invoice_matches.get_by_id.assert_awaited_once_with(
        tenant_id=invoice_match.tenant_id,
        invoice_match_id=invoice_match.id,
        for_update=True,
    )

    coordinator.approvals.get_by_object.assert_awaited_once_with(
        tenant_id=invoice_match.tenant_id,
        object_type=ApprovalObjectType.INVOICE_MATCH,
        object_id=invoice_match.id,
        for_update=True,
    )

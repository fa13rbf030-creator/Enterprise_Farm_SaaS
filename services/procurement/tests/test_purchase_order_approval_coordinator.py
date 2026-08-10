from datetime import UTC, datetime
from unittest.mock import AsyncMock
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
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.purchase_order_approval_coordinator import (
    DuplicatePurchaseOrderApprovalError,
    PurchaseOrderApprovalCoordinator,
    PurchaseOrderApprovalCoordinatorError,
    PurchaseOrderApprovalNotFoundError,
    PurchaseOrderNotFoundError,
)


def make_po(
    *,
    tenant_id=None,
    status=PurchaseOrderStatus.DRAFT,
):
    tenant_id = tenant_id or uuid4()

    return PurchaseOrder(
        id=uuid4(),
        tenant_id=tenant_id,
        po_number=f"PO-{uuid4()}",
        supplier_id=uuid4(),
        order_date=datetime.now(UTC).date(),
        requested_by=uuid4(),
        status=status,
    )


def make_payload(po, *, object_type=None, object_id=None):
    return ProcurementApprovalRequestCreate(
        object_type=(
            object_type or ApprovalObjectType.PURCHASE_ORDER
        ),
        object_id=object_id or po.id,
        requested_by=po.requested_by,
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
                approver_id=uuid4(),
            )
        ],
    )


def make_approval(
    po,
    *,
    status=ApprovalRequestStatus.PENDING,
):
    now = datetime.now(UTC)

    approval = ProcurementApprovalRequest(
        id=uuid4(),
        tenant_id=po.tenant_id,
        object_type=ApprovalObjectType.PURCHASE_ORDER,
        object_id=po.id,
        status=status,
        requested_by=po.requested_by,
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
        PurchaseOrderApprovalCoordinator
    )

    coordinator.session = AsyncMock()
    coordinator.purchase_orders = AsyncMock()
    coordinator.approvals = AsyncMock()

    return coordinator


@pytest.mark.asyncio
async def test_submit_coordinates_purchase_order_and_approval():
    po = make_po()
    coordinator = make_coordinator()

    coordinator.purchase_orders.get_by_id.return_value = po
    coordinator.approvals.get_by_object.return_value = None

    result_po, approval = await coordinator.submit_for_approval(
        tenant_id=po.tenant_id,
        purchase_order_id=po.id,
        payload=make_payload(po),
    )

    assert result_po is po
    assert po.status == PurchaseOrderStatus.PENDING_APPROVAL
    assert approval.status == ApprovalRequestStatus.PENDING
    assert approval.object_id == po.id

    coordinator.approvals.add.assert_awaited_once_with(
        approval
    )


@pytest.mark.asyncio
async def test_submit_rejects_duplicate_approval():
    po = make_po()
    coordinator = make_coordinator()

    coordinator.purchase_orders.get_by_id.return_value = po
    coordinator.approvals.get_by_object.return_value = (
        make_approval(po)
    )

    with pytest.raises(
        DuplicatePurchaseOrderApprovalError
    ):
        await coordinator.submit_for_approval(
            tenant_id=po.tenant_id,
            purchase_order_id=po.id,
            payload=make_payload(po),
        )

    assert po.status == PurchaseOrderStatus.DRAFT


@pytest.mark.asyncio
async def test_submit_rejects_missing_purchase_order():
    po = make_po()
    coordinator = make_coordinator()

    coordinator.purchase_orders.get_by_id.return_value = None

    with pytest.raises(PurchaseOrderNotFoundError):
        await coordinator.submit_for_approval(
            tenant_id=po.tenant_id,
            purchase_order_id=po.id,
            payload=make_payload(po),
        )


@pytest.mark.asyncio
async def test_submit_rejects_wrong_object_type():
    po = make_po()
    coordinator = make_coordinator()

    with pytest.raises(
        PurchaseOrderApprovalCoordinatorError
    ):
        await coordinator.submit_for_approval(
            tenant_id=po.tenant_id,
            purchase_order_id=po.id,
            payload=make_payload(
                po,
                object_type=(
                    ApprovalObjectType.PURCHASE_REQUISITION
                ),
            ),
        )

    coordinator.purchase_orders.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_submit_rejects_wrong_object_id():
    po = make_po()
    coordinator = make_coordinator()

    with pytest.raises(
        PurchaseOrderApprovalCoordinatorError
    ):
        await coordinator.submit_for_approval(
            tenant_id=po.tenant_id,
            purchase_order_id=po.id,
            payload=make_payload(
                po,
                object_id=uuid4(),
            ),
        )


@pytest.mark.asyncio
async def test_decision_rejects_missing_approval():
    po = make_po(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    coordinator = make_coordinator()

    coordinator.purchase_orders.get_by_id.return_value = po
    coordinator.approvals.get_by_object.return_value = None

    with pytest.raises(
        PurchaseOrderApprovalNotFoundError
    ):
        await coordinator.approve_step(
            tenant_id=po.tenant_id,
            purchase_order_id=po.id,
            step_number=1,
            decision=ProcurementApprovalStepDecision(
                decided_by=uuid4(),
            ),
        )


@pytest.mark.asyncio
async def test_load_for_decision_uses_tenant_scoped_locks():
    po = make_po(
        status=PurchaseOrderStatus.PENDING_APPROVAL
    )
    approval = make_approval(po)
    coordinator = make_coordinator()

    coordinator.purchase_orders.get_by_id.return_value = po
    coordinator.approvals.get_by_object.return_value = approval

    loaded_po, loaded_approval = (
        await coordinator._load_for_decision(
            tenant_id=po.tenant_id,
            purchase_order_id=po.id,
        )
    )

    assert loaded_po is po
    assert loaded_approval is approval

    coordinator.purchase_orders.get_by_id.assert_awaited_once_with(
        tenant_id=po.tenant_id,
        purchase_order_id=po.id,
        for_update=True,
    )

    coordinator.approvals.get_by_object.assert_awaited_once_with(
        tenant_id=po.tenant_id,
        object_type=ApprovalObjectType.PURCHASE_ORDER,
        object_id=po.id,
        for_update=True,
    )

from datetime import UTC, datetime
from unittest.mock import AsyncMock
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
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.requisition_approval_coordinator import (
    DuplicateRequisitionApprovalError,
    RequisitionApprovalCoordinator,
    RequisitionApprovalCoordinatorError,
    RequisitionApprovalNotFoundError,
    RequisitionNotFoundError,
)


def make_requisition(
    *,
    tenant_id=None,
    status=RequisitionStatus.DRAFT,
):
    tenant_id = tenant_id or uuid4()

    return PurchaseRequisition(
        id=uuid4(),
        tenant_id=tenant_id,
        requisition_number=f"PR-{uuid4()}",
        requester_id=uuid4(),
        purpose="coordinator unit test",
        status=status,
    )


def make_payload(
    requisition,
    *,
    object_type=ApprovalObjectType.PURCHASE_REQUISITION,
    object_id=None,
):
    return ProcurementApprovalRequestCreate(
        object_type=object_type,
        object_id=object_id or requisition.id,
        requested_by=requisition.requester_id,
        comments="coordinator test approval",
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
                approver_id=uuid4(),
            )
        ],
    )


def make_approval(
    requisition,
    *,
    status=ApprovalRequestStatus.PENDING,
):
    now = datetime.now(UTC)

    approval = ProcurementApprovalRequest(
        id=uuid4(),
        tenant_id=requisition.tenant_id,
        object_type=ApprovalObjectType.PURCHASE_REQUISITION,
        object_id=requisition.id,
        status=status,
        requested_by=requisition.requester_id,
        requested_at=now,
        completed_at=None,
        current_step=1,
        total_steps=1,
        comments="coordinator test approval",
        created_at=now,
        updated_at=now,
    )

    approval.steps = []

    return approval


def make_coordinator():
    coordinator = object.__new__(
        RequisitionApprovalCoordinator
    )

    coordinator.session = AsyncMock()
    coordinator.requisitions = AsyncMock()
    coordinator.approvals = AsyncMock()

    return coordinator


@pytest.mark.asyncio
async def test_submit_for_approval_coordinates_both_aggregates():
    tenant_id = uuid4()
    requisition = make_requisition(
        tenant_id=tenant_id
    )

    coordinator = make_coordinator()

    coordinator.requisitions.get_by_id.return_value = (
        requisition
    )

    coordinator.approvals.get_by_object.return_value = None

    payload = make_payload(requisition)

    result_requisition, approval = (
        await coordinator.submit_for_approval(
            tenant_id=tenant_id,
            requisition_id=requisition.id,
            payload=payload,
        )
    )

    assert result_requisition is requisition
    assert requisition.status == RequisitionStatus.SUBMITTED

    assert (
        approval.status
        == ApprovalRequestStatus.PENDING
    )

    assert approval.object_id == requisition.id

    coordinator.approvals.add.assert_awaited_once_with(
        approval
    )
    coordinator.requisitions.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_rejects_duplicate_approval():
    tenant_id = uuid4()
    requisition = make_requisition(
        tenant_id=tenant_id
    )

    coordinator = make_coordinator()

    coordinator.requisitions.get_by_id.return_value = (
        requisition
    )

    coordinator.approvals.get_by_object.return_value = (
        make_approval(requisition)
    )

    with pytest.raises(
        DuplicateRequisitionApprovalError
    ):
        await coordinator.submit_for_approval(
            tenant_id=tenant_id,
            requisition_id=requisition.id,
            payload=make_payload(requisition),
        )

    assert requisition.status == RequisitionStatus.DRAFT

    coordinator.approvals.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_submit_rejects_missing_requisition():
    tenant_id = uuid4()
    requisition = make_requisition(
        tenant_id=tenant_id
    )

    coordinator = make_coordinator()

    coordinator.requisitions.get_by_id.return_value = None

    with pytest.raises(RequisitionNotFoundError):
        await coordinator.submit_for_approval(
            tenant_id=tenant_id,
            requisition_id=requisition.id,
            payload=make_payload(requisition),
        )


@pytest.mark.asyncio
async def test_submit_rejects_wrong_object_type():
    requisition = make_requisition()
    coordinator = make_coordinator()

    payload = make_payload(
        requisition,
        object_type=ApprovalObjectType.PURCHASE_ORDER,
    )

    with pytest.raises(
        RequisitionApprovalCoordinatorError
    ):
        await coordinator.submit_for_approval(
            tenant_id=requisition.tenant_id,
            requisition_id=requisition.id,
            payload=payload,
        )

    coordinator.requisitions.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_submit_rejects_wrong_object_id():
    requisition = make_requisition()
    coordinator = make_coordinator()

    payload = make_payload(
        requisition,
        object_id=uuid4(),
    )

    with pytest.raises(
        RequisitionApprovalCoordinatorError
    ):
        await coordinator.submit_for_approval(
            tenant_id=requisition.tenant_id,
            requisition_id=requisition.id,
            payload=payload,
        )

    coordinator.requisitions.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_decision_rejects_missing_approval():
    requisition = make_requisition(
        status=RequisitionStatus.SUBMITTED
    )

    coordinator = make_coordinator()

    coordinator.requisitions.get_by_id.return_value = (
        requisition
    )

    coordinator.approvals.get_by_object.return_value = None

    with pytest.raises(
        RequisitionApprovalNotFoundError
    ):
        await coordinator.approve_step(
            tenant_id=requisition.tenant_id,
            requisition_id=requisition.id,
            step_number=1,
            decision=ProcurementApprovalStepDecision(
                decided_by=uuid4(),
            ),
        )


@pytest.mark.asyncio
async def test_load_for_decision_uses_tenant_scoped_locks():
    tenant_id = uuid4()

    requisition = make_requisition(
        tenant_id=tenant_id,
        status=RequisitionStatus.SUBMITTED,
    )

    approval = make_approval(requisition)

    coordinator = make_coordinator()

    coordinator.requisitions.get_by_id.return_value = (
        requisition
    )

    coordinator.approvals.get_by_object.return_value = (
        approval
    )

    loaded_requisition, loaded_approval = (
        await coordinator._load_for_decision(
            tenant_id=tenant_id,
            requisition_id=requisition.id,
        )
    )

    assert loaded_requisition is requisition
    assert loaded_approval is approval

    coordinator.requisitions.get_by_id.assert_awaited_once_with(
        tenant_id=tenant_id,
        requisition_id=requisition.id,
        for_update=True,
    )

    coordinator.approvals.get_by_object.assert_awaited_once_with(
        tenant_id=tenant_id,
        object_type=ApprovalObjectType.PURCHASE_REQUISITION,
        object_id=requisition.id,
        for_update=True,
    )

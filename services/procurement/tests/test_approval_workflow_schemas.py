from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    ApprovalStepStatus,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCancel,
    ProcurementApprovalRequestCreate,
    ProcurementApprovalRequestRead,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
    ProcurementApprovalStepRead,
)


def test_step_create_positive_number():
    value = ProcurementApprovalStepCreate(
        step_number=1,
        approver_id=uuid4(),
    )

    assert value.step_number == 1


def test_step_create_rejects_zero():
    with pytest.raises(ValidationError):
        ProcurementApprovalStepCreate(
            step_number=0,
        )


def test_request_requires_steps():
    with pytest.raises(ValidationError):
        ProcurementApprovalRequestCreate(
            object_type=ApprovalObjectType.PURCHASE_ORDER,
            object_id=uuid4(),
            requested_by=uuid4(),
            steps=[],
        )


def test_request_rejects_duplicate_step_numbers():
    with pytest.raises(ValidationError):
        ProcurementApprovalRequestCreate(
            object_type=ApprovalObjectType.PURCHASE_ORDER,
            object_id=uuid4(),
            requested_by=uuid4(),
            steps=[
                ProcurementApprovalStepCreate(
                    step_number=1,
                ),
                ProcurementApprovalStepCreate(
                    step_number=1,
                ),
            ],
        )


def test_request_rejects_non_contiguous_steps():
    with pytest.raises(ValidationError):
        ProcurementApprovalRequestCreate(
            object_type=ApprovalObjectType.PURCHASE_ORDER,
            object_id=uuid4(),
            requested_by=uuid4(),
            steps=[
                ProcurementApprovalStepCreate(
                    step_number=1,
                ),
                ProcurementApprovalStepCreate(
                    step_number=3,
                ),
            ],
        )


def test_request_accepts_contiguous_steps():
    value = ProcurementApprovalRequestCreate(
        object_type=ApprovalObjectType.PURCHASE_ORDER,
        object_id=uuid4(),
        requested_by=uuid4(),
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
            ),
            ProcurementApprovalStepCreate(
                step_number=2,
            ),
        ],
    )

    assert value.steps[1].step_number == 2


def test_extra_input_is_forbidden():
    with pytest.raises(ValidationError):
        ProcurementApprovalStepCreate(
            step_number=1,
            unexpected=True,
        )


def test_decision_requires_actor():
    actor = uuid4()

    value = ProcurementApprovalStepDecision(
        decided_by=actor,
        comments="approved",
    )

    assert value.decided_by == actor


def test_comment_length_gate():
    with pytest.raises(ValidationError):
        ProcurementApprovalRequestCancel(
            comments="x" * 2001,
        )


def test_read_contract_matches_domain():
    now = datetime.now(timezone.utc)

    tenant_id = uuid4()
    request_id = uuid4()

    step = ProcurementApprovalStepRead(
        id=uuid4(),
        tenant_id=tenant_id,
        approval_request_id=request_id,
        step_number=1,
        status=ApprovalStepStatus.PENDING,
        approver_id=uuid4(),
        decided_by=None,
        decided_at=None,
        comments=None,
        created_at=now,
        updated_at=now,
    )

    result = ProcurementApprovalRequestRead(
        id=request_id,
        tenant_id=tenant_id,
        object_type=ApprovalObjectType.PURCHASE_ORDER,
        object_id=uuid4(),
        status=ApprovalRequestStatus.PENDING,
        requested_by=uuid4(),
        requested_at=now,
        completed_at=None,
        current_step=1,
        total_steps=1,
        comments=None,
        created_at=now,
        updated_at=now,
        steps=[step],
    )

    assert result.id == request_id
    assert result.tenant_id == tenant_id
    assert result.current_step == 1
    assert result.total_steps == 1
    assert len(result.steps) == 1

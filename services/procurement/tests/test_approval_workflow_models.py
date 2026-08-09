from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    ApprovalStepStatus,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    ProcurementApprovalStep,
)


def test_approval_object_type_values():
    assert (
        ApprovalObjectType.PURCHASE_REQUISITION.value
        == "PURCHASE_REQUISITION"
    )
    assert (
        ApprovalObjectType.PURCHASE_ORDER.value
        == "PURCHASE_ORDER"
    )
    assert (
        ApprovalObjectType.INVOICE_MATCH.value
        == "INVOICE_MATCH"
    )
    assert (
        ApprovalObjectType.SUPPLIER_RETURN.value
        == "SUPPLIER_RETURN"
    )


def test_approval_request_status_values():
    assert ApprovalRequestStatus.PENDING.value == "PENDING"
    assert ApprovalRequestStatus.IN_PROGRESS.value == "IN_PROGRESS"
    assert ApprovalRequestStatus.APPROVED.value == "APPROVED"
    assert ApprovalRequestStatus.REJECTED.value == "REJECTED"
    assert ApprovalRequestStatus.CANCELLED.value == "CANCELLED"


def test_approval_step_status_values():
    assert ApprovalStepStatus.PENDING.value == "PENDING"
    assert ApprovalStepStatus.APPROVED.value == "APPROVED"
    assert ApprovalStepStatus.REJECTED.value == "REJECTED"
    assert ApprovalStepStatus.SKIPPED.value == "SKIPPED"


def test_approval_request_table_name():
    assert (
        ProcurementApprovalRequest.__tablename__
        == "procurement_approval_requests"
    )


def test_approval_step_table_name():
    assert (
        ProcurementApprovalStep.__tablename__
        == "procurement_approval_steps"
    )


def test_approval_request_tenant_is_required():
    column = (
        ProcurementApprovalRequest.__table__
        .c.tenant_id
    )

    assert column.nullable is False


def test_approval_step_tenant_is_required():
    column = (
        ProcurementApprovalStep.__table__
        .c.tenant_id
    )

    assert column.nullable is False


def test_approval_request_object_is_required():
    table = ProcurementApprovalRequest.__table__

    assert table.c.object_type.nullable is False
    assert table.c.object_id.nullable is False


def test_approval_step_parent_fk_exists():
    column = (
        ProcurementApprovalStep.__table__
        .c.approval_request_id
    )

    foreign_keys = list(column.foreign_keys)

    assert len(foreign_keys) == 1

    fk = foreign_keys[0]

    assert (
        fk.target_fullname
        == "procurement_approval_requests.id"
    )

    assert fk.ondelete == "CASCADE"


def test_approval_relationships_exist():
    assert "steps" in ProcurementApprovalRequest.__mapper__.relationships
    assert (
        "approval_request"
        in ProcurementApprovalStep.__mapper__.relationships
    )


def test_approval_request_unique_object_constraint():
    constraints = {
        constraint.name
        for constraint
        in ProcurementApprovalRequest.__table__.constraints
    }

    assert "uq_proc_approval_object" in constraints


def test_approval_step_unique_number_constraint():
    constraints = {
        constraint.name
        for constraint
        in ProcurementApprovalStep.__table__.constraints
    }

    assert "uq_proc_approval_step_number" in constraints

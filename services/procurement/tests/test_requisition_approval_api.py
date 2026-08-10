from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from procurement_service.api import (
    requisition_approvals as api,
)
from procurement_service.core.config import get_settings
from procurement_service.core.enums import ApprovalObjectType
from procurement_service.db.session import get_db_session
from procurement_service.main import app
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.requisition_approval_coordinator import (
    DuplicateRequisitionApprovalError,
)


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


async def override_db_session():
    yield FakeSession()


def token(
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)

    return jwt.encode(
        {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "access",
            "iss": settings.token_issuer,
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=5),
            "jti": str(uuid4()),
            "permissions": permissions,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def headers(
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
    header_tenant_id: UUID | None = None,
):
    return {
        "Authorization": (
            "Bearer "
            + token(
                user_id=user_id,
                tenant_id=tenant_id,
                permissions=permissions,
            )
        ),
        "X-Tenant-ID": str(
            header_tenant_id or tenant_id
        ),
    }


def create_payload(
    *,
    requisition_id: UUID,
    requested_by: UUID,
):
    return ProcurementApprovalRequestCreate(
        object_type=ApprovalObjectType.PURCHASE_REQUISITION,
        object_id=requisition_id,
        requested_by=requested_by,
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
                approver_id=uuid4(),
            )
        ],
    ).model_dump(mode="json")


def decision_payload(*, decided_by: UUID):
    return ProcurementApprovalStepDecision(
        decided_by=decided_by,
        comments="R3E-B API test",
    ).model_dump(mode="json")


@pytest.fixture(autouse=True)
def dependencies():
    app.dependency_overrides[
        get_db_session
    ] = override_db_session

    yield

    app.dependency_overrides.clear()


def test_openapi_registers_requisition_approval_paths():
    document = app.openapi()

    expected = {
        (
            "/purchase-requisitions/{requisition_id}"
            "/submit-for-approval"
        ),
        (
            "/purchase-requisitions/{requisition_id}"
            "/approval-steps/{step_number}/approve"
        ),
        (
            "/purchase-requisitions/{requisition_id}"
            "/approval-steps/{step_number}/reject"
        ),
    }

    assert expected <= set(document["paths"])


def test_submit_requires_authentication():
    requisition_id = uuid4()

    response = TestClient(app).post(
        (
            f"/purchase-requisitions/{requisition_id}"
            "/submit-for-approval"
        ),
        headers={
            "X-Tenant-ID": str(uuid4()),
        },
        json=create_payload(
            requisition_id=requisition_id,
            requested_by=uuid4(),
        ),
    )

    assert response.status_code == 401


def test_submit_requires_create_permission():
    requisition_id = uuid4()
    user_id = uuid4()
    tenant_id = uuid4()

    response = TestClient(app).post(
        (
            f"/purchase-requisitions/{requisition_id}"
            "/submit-for-approval"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.read"
            ],
        ),
        json=create_payload(
            requisition_id=requisition_id,
            requested_by=user_id,
        ),
    )

    assert response.status_code == 403


def test_submit_rejects_cross_tenant():
    requisition_id = uuid4()
    user_id = uuid4()

    response = TestClient(app).post(
        (
            f"/purchase-requisitions/{requisition_id}"
            "/submit-for-approval"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=uuid4(),
            header_tenant_id=uuid4(),
            permissions=[
                "procurement.approvals.create"
            ],
        ),
        json=create_payload(
            requisition_id=requisition_id,
            requested_by=user_id,
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant access denied"
    )


def test_submit_rejects_actor_spoof():
    requisition_id = uuid4()
    user_id = uuid4()
    tenant_id = uuid4()

    response = TestClient(app).post(
        (
            f"/purchase-requisitions/{requisition_id}"
            "/submit-for-approval"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.create"
            ],
        ),
        json=create_payload(
            requisition_id=requisition_id,
            requested_by=uuid4(),
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "requested_by must match authenticated user"
    )


def test_approve_rejects_actor_spoof():
    user_id = uuid4()
    tenant_id = uuid4()

    response = TestClient(app).post(
        (
            f"/purchase-requisitions/{uuid4()}"
            "/approval-steps/1/approve"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.approve"
            ],
        ),
        json=decision_payload(
            decided_by=uuid4()
        ),
    )

    assert response.status_code == 403


def test_reject_rejects_actor_spoof():
    user_id = uuid4()
    tenant_id = uuid4()

    response = TestClient(app).post(
        (
            f"/purchase-requisitions/{uuid4()}"
            "/approval-steps/1/reject"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.reject"
            ],
        ),
        json=decision_payload(
            decided_by=uuid4()
        ),
    )

    assert response.status_code == 403


def test_global_override_reaches_coordinator(monkeypatch):
    class FakeCoordinator:
        def __init__(self, session):
            self.session = session

        async def submit_for_approval(self, **kwargs):
            raise DuplicateRequisitionApprovalError(
                "duplicate approval"
            )

    monkeypatch.setattr(
        api,
        "RequisitionApprovalCoordinator",
        FakeCoordinator,
    )

    requisition_id = uuid4()

    response = TestClient(app).post(
        (
            f"/purchase-requisitions/{requisition_id}"
            "/submit-for-approval"
        ),
        headers=headers(
            user_id=uuid4(),
            tenant_id=uuid4(),
            header_tenant_id=uuid4(),
            permissions=["*"],
        ),
        json=create_payload(
            requisition_id=requisition_id,
            requested_by=uuid4(),
        ),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "duplicate approval"
    )

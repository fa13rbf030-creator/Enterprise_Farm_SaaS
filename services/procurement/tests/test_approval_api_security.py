from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from procurement_service.api import approvals as approvals_api
from procurement_service.core.config import get_settings
from procurement_service.core.enums import ApprovalObjectType
from procurement_service.db.session import get_db_session
from procurement_service.main import app
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
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


def make_access_token(
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "access",
        "iss": settings.token_issuer,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
        "jti": str(uuid4()),
        "permissions": permissions,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def auth_headers(
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
    header_tenant_id: UUID | None = None,
) -> dict[str, str]:
    token = make_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        permissions=permissions,
    )

    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(
            header_tenant_id or tenant_id
        ),
    }


def build_step(
    approver_id: UUID,
) -> dict:
    fields = ProcurementApprovalStepCreate.model_fields

    payload: dict[str, object] = {}

    if "step_number" in fields:
        payload["step_number"] = 1

    if "approver_id" in fields:
        payload["approver_id"] = str(approver_id)
    elif "approver_user_id" in fields:
        payload["approver_user_id"] = str(
            approver_id
        )

    model = ProcurementApprovalStepCreate(
        **payload
    )

    return model.model_dump(
        mode="json"
    )


def build_create_payload(
    *,
    requested_by: UUID,
) -> dict:
    model = ProcurementApprovalRequestCreate(
        object_type=ApprovalObjectType.PURCHASE_ORDER,
        object_id=uuid4(),
        requested_by=requested_by,
        steps=[
            build_step(uuid4())
        ],
    )

    return model.model_dump(
        mode="json"
    )


def build_decision_payload(
    *,
    decided_by: UUID,
) -> dict:
    fields = ProcurementApprovalStepDecision.model_fields

    payload: dict[str, object] = {}

    if "decided_by" in fields:
        payload["decided_by"] = decided_by

    if "comments" in fields:
        payload["comments"] = "API security test"

    if "decision_note" in fields:
        payload["decision_note"] = (
            "API security test"
        )

    model = ProcurementApprovalStepDecision(
        **payload
    )

    return model.model_dump(
        mode="json"
    )


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    app.dependency_overrides[
        get_db_session
    ] = override_db_session

    yield

    app.dependency_overrides.clear()


def test_create_requires_bearer_authentication():
    client = TestClient(app)

    response = client.post(
        "/approvals",
        headers={
            "X-Tenant-ID": str(uuid4()),
        },
        json=build_create_payload(
            requested_by=uuid4(),
        ),
    )

    assert response.status_code == 401


def test_create_rejects_missing_permission():
    client = TestClient(app)

    user_id = uuid4()
    tenant_id = uuid4()

    response = client.post(
        "/approvals",
        headers=auth_headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.read",
            ],
        ),
        json=build_create_payload(
            requested_by=user_id,
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Missing permission: "
        "procurement.approvals.create"
    )


def test_create_rejects_cross_tenant_access():
    client = TestClient(app)

    user_id = uuid4()

    response = client.post(
        "/approvals",
        headers=auth_headers(
            user_id=user_id,
            tenant_id=uuid4(),
            header_tenant_id=uuid4(),
            permissions=[
                "procurement.approvals.create",
            ],
        ),
        json=build_create_payload(
            requested_by=user_id,
        ),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Tenant access denied"
    )


def test_create_rejects_requested_by_spoof():
    client = TestClient(app)

    user_id = uuid4()
    tenant_id = uuid4()

    response = client.post(
        "/approvals",
        headers=auth_headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.create",
            ],
        ),
        json=build_create_payload(
            requested_by=uuid4(),
        ),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "requested_by must match "
        "authenticated user"
    )


def test_approve_rejects_decided_by_spoof():
    client = TestClient(app)

    user_id = uuid4()
    tenant_id = uuid4()

    response = client.post(
        (
            f"/approvals/{uuid4()}"
            "/steps/1/approve"
        ),
        headers=auth_headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.approve",
            ],
        ),
        json=build_decision_payload(
            decided_by=uuid4(),
        ),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "decided_by must match "
        "authenticated user"
    )


def test_reject_rejects_decided_by_spoof():
    client = TestClient(app)

    user_id = uuid4()
    tenant_id = uuid4()

    response = client.post(
        (
            f"/approvals/{uuid4()}"
            "/steps/1/reject"
        ),
        headers=auth_headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.reject",
            ],
        ),
        json=build_decision_payload(
            decided_by=uuid4(),
        ),
    )

    assert response.status_code == 403


def test_global_override_allows_cross_tenant_and_actor_override(
    monkeypatch,
):
    class DuplicateRepository:
        def __init__(self, session):
            self.session = session

        async def get_by_object(
            self,
            *,
            tenant_id,
            object_type,
            object_id,
        ):
            return object()

    monkeypatch.setattr(
        approvals_api,
        "ProcurementApprovalRepository",
        DuplicateRepository,
    )

    client = TestClient(app)

    ceo_user_id = uuid4()

    response = client.post(
        "/approvals",
        headers=auth_headers(
            user_id=ceo_user_id,
            tenant_id=uuid4(),
            header_tenant_id=uuid4(),
            permissions=["*"],
        ),
        json=build_create_payload(
            requested_by=uuid4(),
        ),
    )

    # 409 proves the request passed:
    # - global permission override;
    # - cross-tenant override;
    # - requested_by actor override;
    # and reached the repository duplicate gate.
    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Approval request already exists "
        "for object"
    )

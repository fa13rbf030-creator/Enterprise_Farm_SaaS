from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from procurement_service.api import (
    invoice_match_approvals as api,
)
from procurement_service.core.config import get_settings
from procurement_service.db.session import get_db_session
from procurement_service.main import app
from procurement_service.services.invoice_match_approval_coordinator import (
    DuplicateInvoiceMatchApprovalError,
    InvoiceMatchApprovalNotFoundError,
    InvoiceMatchNotFoundError,
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
    ceo_override: bool = False,
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
        "exp": now + timedelta(minutes=15),
        "jti": str(uuid4()),
        "permissions": (
            ["*"]
            if ceo_override
            else permissions
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def headers(
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
    ceo_override: bool = False,
) -> dict[str, str]:
    return {
        "Authorization": (
            "Bearer "
            + token(
                user_id=user_id,
                tenant_id=tenant_id,
                permissions=permissions,
                ceo_override=ceo_override,
            )
        ),
        "X-Tenant-ID": str(tenant_id),
    }


def submission_payload(
    *,
    invoice_match_id: UUID,
    requested_by: UUID,
) -> dict:
    return {
        "object_type": "INVOICE_MATCH",
        "object_id": str(invoice_match_id),
        "requested_by": str(requested_by),
        "comments": "API invoice match approval",
        "steps": [
            {
                "step_number": 1,
                "approver_id": str(uuid4()),
            }
        ],
    }


def decision_payload(*, decided_by: UUID) -> dict:
    return {
        "decided_by": str(decided_by),
        "comments": "API decision",
    }


@pytest.fixture(autouse=True)
def dependencies():
    app.dependency_overrides[get_db_session] = (
        override_db_session
    )

    yield

    app.dependency_overrides.clear()


def test_invoice_match_routes_are_registered():
    document = app.openapi()

    expected = {
        (
            "/invoice-matches/{invoice_match_id}"
            "/submit-for-approval"
        ),
        (
            "/invoice-matches/{invoice_match_id}"
            "/approval-steps/{step_number}/approve"
        ),
        (
            "/invoice-matches/{invoice_match_id}"
            "/approval-steps/{step_number}/reject"
        ),
    }

    actual = {
        path
        for path in document["paths"]
        if path.startswith("/invoice-matches")
    }

    assert expected <= actual


def test_submit_requires_authentication():
    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{uuid4()}"
            "/submit-for-approval"
        ),
        json=submission_payload(
            invoice_match_id=uuid4(),
            requested_by=uuid4(),
        ),
    )

    assert response.status_code == 401


def test_submit_requires_create_permission():
    tenant_id = uuid4()
    user_id = uuid4()
    invoice_match_id = uuid4()

    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{invoice_match_id}"
            "/submit-for-approval"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[],
        ),
        json=submission_payload(
            invoice_match_id=invoice_match_id,
            requested_by=user_id,
        ),
    )

    assert response.status_code == 403


def test_submit_rejects_actor_spoofing():
    tenant_id = uuid4()
    user_id = uuid4()
    invoice_match_id = uuid4()

    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{invoice_match_id}"
            "/submit-for-approval"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.create",
            ],
        ),
        json=submission_payload(
            invoice_match_id=invoice_match_id,
            requested_by=uuid4(),
        ),
    )

    assert response.status_code == 403


def test_approve_requires_approve_permission():
    tenant_id = uuid4()
    user_id = uuid4()

    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{uuid4()}"
            "/approval-steps/1/approve"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[],
        ),
        json=decision_payload(
            decided_by=user_id,
        ),
    )

    assert response.status_code == 403


def test_reject_requires_reject_permission():
    tenant_id = uuid4()
    user_id = uuid4()

    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{uuid4()}"
            "/approval-steps/1/reject"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[],
        ),
        json=decision_payload(
            decided_by=user_id,
        ),
    )

    assert response.status_code == 403


def test_approve_rejects_actor_spoofing():
    tenant_id = uuid4()
    user_id = uuid4()

    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{uuid4()}"
            "/approval-steps/1/approve"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.approve",
            ],
        ),
        json=decision_payload(
            decided_by=uuid4(),
        ),
    )

    assert response.status_code == 403


def test_ceo_override_allows_actor_override(monkeypatch):
    tenant_id = uuid4()
    user_id = uuid4()
    invoice_match_id = uuid4()

    class FakeCoordinator:
        def __init__(self, session):
            self.session = session

        async def submit_for_approval(self, **kwargs):
            raise DuplicateInvoiceMatchApprovalError(
                "duplicate approval"
            )

    monkeypatch.setattr(
        api,
        "InvoiceMatchApprovalCoordinator",
        FakeCoordinator,
    )

    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{invoice_match_id}"
            "/submit-for-approval"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.create",
            ],
            ceo_override=True,
        ),
        json=submission_payload(
            invoice_match_id=invoice_match_id,
            requested_by=uuid4(),
        ),
    )

    assert response.status_code == 409


def test_missing_invoice_match_maps_to_404(monkeypatch):
    tenant_id = uuid4()
    user_id = uuid4()
    invoice_match_id = uuid4()

    class FakeCoordinator:
        def __init__(self, session):
            self.session = session

        async def submit_for_approval(self, **kwargs):
            raise InvoiceMatchNotFoundError(
                "invoice match not found"
            )

    monkeypatch.setattr(
        api,
        "InvoiceMatchApprovalCoordinator",
        FakeCoordinator,
    )

    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{invoice_match_id}"
            "/submit-for-approval"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.create",
            ],
        ),
        json=submission_payload(
            invoice_match_id=invoice_match_id,
            requested_by=user_id,
        ),
    )

    assert response.status_code == 404


def test_missing_approval_maps_to_404(monkeypatch):
    tenant_id = uuid4()
    user_id = uuid4()
    invoice_match_id = uuid4()

    class FakeCoordinator:
        def __init__(self, session):
            self.session = session

        async def approve_step(self, **kwargs):
            raise InvoiceMatchApprovalNotFoundError(
                "approval not found"
            )

    monkeypatch.setattr(
        api,
        "InvoiceMatchApprovalCoordinator",
        FakeCoordinator,
    )

    client = TestClient(app)

    response = client.post(
        (
            f"/invoice-matches/{invoice_match_id}"
            "/approval-steps/1/approve"
        ),
        headers=headers(
            user_id=user_id,
            tenant_id=tenant_id,
            permissions=[
                "procurement.approvals.approve",
            ],
        ),
        json=decision_payload(
            decided_by=user_id,
        ),
    )

    assert response.status_code == 404

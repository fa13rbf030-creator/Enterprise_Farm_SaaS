from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from procurement_service.core.config import get_settings
from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    RequisitionStatus,
)
from procurement_service.db.session import (
    AsyncSessionFactory,
    engine,
)
from procurement_service.main import app
from procurement_service.models import (
    ProcurementApprovalRequest,
    ProcurementApprovalStep,
    PurchaseRequisition,
)


PURPOSE = "R3E-C HTTP postgres test"
APPROVAL_COMMENT = "R3E-C HTTP approval"


@pytest_asyncio.fixture(
    scope="module",
    loop_scope="module",
    autouse=True,
)
async def isolate_engine_pool():
    await engine.dispose(close=False)

    try:
        yield
    finally:
        await engine.dispose()


def make_token(
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
) -> dict[str, str]:
    return {
        "Authorization": (
            "Bearer "
            + make_token(
                user_id=user_id,
                tenant_id=tenant_id,
                permissions=permissions,
            )
        ),
        "X-Tenant-ID": str(tenant_id),
    }


async def create_requisition(
    *,
    tenant_id: UUID,
    requester_id: UUID,
) -> PurchaseRequisition:
    requisition = PurchaseRequisition(
        id=uuid4(),
        tenant_id=tenant_id,
        requisition_number=f"R3EC-{uuid4()}",
        requester_id=requester_id,
        purpose=PURPOSE,
        status=RequisitionStatus.DRAFT,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async with AsyncSessionFactory() as session:
        session.add(requisition)
        await session.commit()

    return requisition


async def cleanup(
    requisition_id: UUID,
) -> None:
    async with AsyncSessionFactory() as session:
        approval_ids = (
            await session.scalars(
                select(ProcurementApprovalRequest.id).where(
                    ProcurementApprovalRequest.object_type
                    == ApprovalObjectType.PURCHASE_REQUISITION,
                    ProcurementApprovalRequest.object_id
                    == requisition_id,
                )
            )
        ).all()

        if approval_ids:
            await session.execute(
                delete(ProcurementApprovalStep).where(
                    ProcurementApprovalStep.approval_request_id.in_(
                        approval_ids
                    )
                )
            )

            await session.execute(
                delete(ProcurementApprovalRequest).where(
                    ProcurementApprovalRequest.id.in_(
                        approval_ids
                    )
                )
            )

        await session.execute(
            delete(PurchaseRequisition).where(
                PurchaseRequisition.id == requisition_id
            )
        )

        await session.commit()


async def load_requisition(
    requisition_id: UUID,
):
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(PurchaseRequisition).where(
                PurchaseRequisition.id == requisition_id
            )
        )


async def load_approval(
    requisition_id: UUID,
):
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(ProcurementApprovalRequest).where(
                ProcurementApprovalRequest.object_type
                == ApprovalObjectType.PURCHASE_REQUISITION,
                ProcurementApprovalRequest.object_id
                == requisition_id,
            )
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_http_submit_and_approve_persists_terminal_state():
    tenant_id = uuid4()
    requester_id = uuid4()
    approver_id = uuid4()

    requisition = await create_requisition(
        tenant_id=tenant_id,
        requester_id=requester_id,
    )

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            submit = await client.post(
                (
                    f"/purchase-requisitions/{requisition.id}"
                    "/submit-for-approval"
                ),
                headers=headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create"
                    ],
                ),
                json={
                    "object_type": "PURCHASE_REQUISITION",
                    "object_id": str(requisition.id),
                    "requested_by": str(requester_id),
                    "comments": APPROVAL_COMMENT,
                    "steps": [
                        {
                            "step_number": 1,
                            "approver_id": str(approver_id),
                        }
                    ],
                },
            )

            assert submit.status_code == 201, submit.text

            submitted = submit.json()

            assert submitted["status"] == "PENDING"
            assert (
                submitted["object_type"]
                == "PURCHASE_REQUISITION"
            )

            persisted = await load_requisition(
                requisition.id
            )

            assert persisted is not None
            assert (
                persisted.status
                == RequisitionStatus.SUBMITTED
            )

            approve = await client.post(
                (
                    f"/purchase-requisitions/{requisition.id}"
                    "/approval-steps/1/approve"
                ),
                headers=headers(
                    user_id=approver_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.approve"
                    ],
                ),
                json={
                    "decided_by": str(approver_id),
                    "comments": "R3E-C approved",
                },
            )

            assert approve.status_code == 200, approve.text

            approved = approve.json()

            assert approved["status"] == "APPROVED"

        persisted = await load_requisition(requisition.id)
        approval = await load_approval(requisition.id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.APPROVED
        assert persisted.approved_by == approver_id
        assert persisted.approved_at is not None

        assert approval is not None
        assert (
            approval.status
            == ApprovalRequestStatus.APPROVED
        )

    finally:
        await cleanup(requisition.id)


@pytest.mark.asyncio(loop_scope="module")
async def test_http_reject_persists_rejection_reason():
    tenant_id = uuid4()
    requester_id = uuid4()
    approver_id = uuid4()

    requisition = await create_requisition(
        tenant_id=tenant_id,
        requester_id=requester_id,
    )

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            submit = await client.post(
                (
                    f"/purchase-requisitions/{requisition.id}"
                    "/submit-for-approval"
                ),
                headers=headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create"
                    ],
                ),
                json={
                    "object_type": "PURCHASE_REQUISITION",
                    "object_id": str(requisition.id),
                    "requested_by": str(requester_id),
                    "comments": APPROVAL_COMMENT,
                    "steps": [
                        {
                            "step_number": 1,
                            "approver_id": str(approver_id),
                        }
                    ],
                },
            )

            assert submit.status_code == 201, submit.text

            reject = await client.post(
                (
                    f"/purchase-requisitions/{requisition.id}"
                    "/approval-steps/1/reject"
                ),
                headers=headers(
                    user_id=approver_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.reject"
                    ],
                ),
                json={
                    "decided_by": str(approver_id),
                    "comments": "Budget unavailable",
                },
            )

            assert reject.status_code == 200, reject.text
            assert reject.json()["status"] == "REJECTED"

        persisted = await load_requisition(requisition.id)
        approval = await load_approval(requisition.id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.REJECTED
        assert persisted.approved_by is None
        assert persisted.approved_at is None
        assert (
            persisted.rejection_reason
            == "Budget unavailable"
        )

        assert approval is not None
        assert (
            approval.status
            == ApprovalRequestStatus.REJECTED
        )

    finally:
        await cleanup(requisition.id)


@pytest.mark.asyncio(loop_scope="module")
async def test_http_duplicate_submission_returns_conflict():
    tenant_id = uuid4()
    requester_id = uuid4()
    approver_id = uuid4()

    requisition = await create_requisition(
        tenant_id=tenant_id,
        requester_id=requester_id,
    )

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            payload = {
                "object_type": "PURCHASE_REQUISITION",
                "object_id": str(requisition.id),
                "requested_by": str(requester_id),
                "comments": APPROVAL_COMMENT,
                "steps": [
                    {
                        "step_number": 1,
                        "approver_id": str(approver_id),
                    }
                ],
            }

            first = await client.post(
                (
                    f"/purchase-requisitions/{requisition.id}"
                    "/submit-for-approval"
                ),
                headers=headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create"
                    ],
                ),
                json=payload,
            )

            assert first.status_code == 201, first.text

            second = await client.post(
                (
                    f"/purchase-requisitions/{requisition.id}"
                    "/submit-for-approval"
                ),
                headers=headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create"
                    ],
                ),
                json=payload,
            )

            assert second.status_code == 409

        approval = await load_approval(requisition.id)

        assert approval is not None

    finally:
        await cleanup(requisition.id)

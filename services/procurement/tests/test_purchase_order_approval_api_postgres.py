from datetime import UTC, datetime, timedelta
from decimal import Decimal
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
    PurchaseOrderStatus,
    SupplierStatus,
)
from procurement_service.db.session import (
    AsyncSessionFactory,
    engine,
)
from procurement_service.main import app
from procurement_service.models import (
    ProcurementApprovalRequest,
    ProcurementApprovalStep,
    ProcurementSupplier,
    PurchaseOrder,
)


PO_NOTE = "R4F HTTP postgres approval integration"
APPROVAL_COMMENT = "R4F HTTP purchase order approval"
SUPPLIER_NAME = "R4F HTTP Integration Supplier"


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
    header_tenant_id: UUID | None = None,
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
        "X-Tenant-ID": str(
            header_tenant_id or tenant_id
        ),
    }


async def create_fixture():
    tenant_id = uuid4()
    requester_id = uuid4()
    now = datetime.now(UTC)

    supplier = ProcurementSupplier(
        id=uuid4(),
        tenant_id=tenant_id,
        supplier_code=f"R4F-{uuid4()}",
        legal_name=SUPPLIER_NAME,
        status=SupplierStatus.ACTIVE,
        created_by=requester_id,
        created_at=now,
        updated_at=now,
    )

    purchase_order = PurchaseOrder(
        id=uuid4(),
        tenant_id=tenant_id,
        po_number=f"R4F-PO-{uuid4()}",
        supplier_id=supplier.id,
        order_date=now.date(),
        currency_code="USD",
        subtotal_amount=Decimal("100.000000"),
        discount_amount=Decimal("0.000000"),
        tax_amount=Decimal("10.000000"),
        total_amount=Decimal("110.000000"),
        notes=PO_NOTE,
        requested_by=requester_id,
        status=PurchaseOrderStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )

    async with AsyncSessionFactory() as session:
        session.add(supplier)
        session.add(purchase_order)
        await session.commit()

    return tenant_id, requester_id, supplier, purchase_order


async def cleanup(
    *,
    purchase_order_id: UUID,
    supplier_id: UUID,
) -> None:
    async with AsyncSessionFactory() as session:
        approval_ids = (
            await session.scalars(
                select(ProcurementApprovalRequest.id).where(
                    ProcurementApprovalRequest.object_type
                    == ApprovalObjectType.PURCHASE_ORDER,
                    ProcurementApprovalRequest.object_id
                    == purchase_order_id,
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
            delete(PurchaseOrder).where(
                PurchaseOrder.id == purchase_order_id
            )
        )

        await session.execute(
            delete(ProcurementSupplier).where(
                ProcurementSupplier.id == supplier_id
            )
        )

        await session.commit()


async def load_purchase_order(
    purchase_order_id: UUID,
) -> PurchaseOrder | None:
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(PurchaseOrder).where(
                PurchaseOrder.id == purchase_order_id
            )
        )


async def load_approval(
    purchase_order_id: UUID,
) -> ProcurementApprovalRequest | None:
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(ProcurementApprovalRequest).where(
                ProcurementApprovalRequest.object_type
                == ApprovalObjectType.PURCHASE_ORDER,
                ProcurementApprovalRequest.object_id
                == purchase_order_id,
            )
        )


async def approval_count(
    purchase_order_id: UUID,
) -> int:
    async with AsyncSessionFactory() as session:
        rows = (
            await session.scalars(
                select(ProcurementApprovalRequest.id).where(
                    ProcurementApprovalRequest.object_type
                    == ApprovalObjectType.PURCHASE_ORDER,
                    ProcurementApprovalRequest.object_id
                    == purchase_order_id,
                )
            )
        ).all()

        return len(rows)


def submission_payload(
    *,
    purchase_order_id: UUID,
    requested_by: UUID,
    approver_id: UUID,
) -> dict:
    return {
        "object_type": "PURCHASE_ORDER",
        "object_id": str(purchase_order_id),
        "requested_by": str(requested_by),
        "comments": APPROVAL_COMMENT,
        "steps": [
            {
                "step_number": 1,
                "approver_id": str(approver_id),
            }
        ],
    }


@pytest.mark.asyncio(loop_scope="module")
async def test_http_submit_and_approve_purchase_order():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            submit = await client.post(
                (
                    f"/purchase-orders/{purchase_order.id}"
                    "/submit-for-approval"
                ),
                headers=headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create"
                    ],
                ),
                json=submission_payload(
                    purchase_order_id=purchase_order.id,
                    requested_by=requester_id,
                    approver_id=approver_id,
                ),
            )

            assert submit.status_code == 201, submit.text
            assert submit.json()["status"] == "PENDING"

            persisted = await load_purchase_order(
                purchase_order.id
            )

            assert persisted is not None
            assert (
                persisted.status
                == PurchaseOrderStatus.PENDING_APPROVAL
            )

            approve = await client.post(
                (
                    f"/purchase-orders/{purchase_order.id}"
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
                    "comments": "R4F approved",
                },
            )

            assert approve.status_code == 200, approve.text
            assert approve.json()["status"] == "APPROVED"

        persisted = await load_purchase_order(
            purchase_order.id
        )

        approval = await load_approval(
            purchase_order.id
        )

        assert persisted is not None
        assert persisted.status == PurchaseOrderStatus.APPROVED
        assert persisted.approved_by == approver_id
        assert persisted.approved_at is not None

        assert approval is not None
        assert (
            approval.status
            == ApprovalRequestStatus.APPROVED
        )

    finally:
        await cleanup(
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_http_rejection_returns_purchase_order_to_draft():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            submit = await client.post(
                (
                    f"/purchase-orders/{purchase_order.id}"
                    "/submit-for-approval"
                ),
                headers=headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create"
                    ],
                ),
                json=submission_payload(
                    purchase_order_id=purchase_order.id,
                    requested_by=requester_id,
                    approver_id=approver_id,
                ),
            )

            assert submit.status_code == 201, submit.text

            reject = await client.post(
                (
                    f"/purchase-orders/{purchase_order.id}"
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
                    "comments": "R4F rejected",
                },
            )

            assert reject.status_code == 200, reject.text
            assert reject.json()["status"] == "REJECTED"

        persisted = await load_purchase_order(
            purchase_order.id
        )

        approval = await load_approval(
            purchase_order.id
        )

        assert persisted is not None
        assert persisted.status == PurchaseOrderStatus.DRAFT
        assert persisted.approved_by is None
        assert persisted.approved_at is None

        assert approval is not None
        assert (
            approval.status
            == ApprovalRequestStatus.REJECTED
        )

    finally:
        await cleanup(
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_http_duplicate_submission_returns_conflict():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            payload = submission_payload(
                purchase_order_id=purchase_order.id,
                requested_by=requester_id,
                approver_id=approver_id,
            )

            first = await client.post(
                (
                    f"/purchase-orders/{purchase_order.id}"
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
                    f"/purchase-orders/{purchase_order.id}"
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

        assert await approval_count(purchase_order.id) == 1

        persisted = await load_purchase_order(
            purchase_order.id
        )

        assert persisted is not None
        assert (
            persisted.status
            == PurchaseOrderStatus.PENDING_APPROVAL
        )

    finally:
        await cleanup(
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )

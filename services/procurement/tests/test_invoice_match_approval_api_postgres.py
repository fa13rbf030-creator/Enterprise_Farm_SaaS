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
    InvoiceMatchExceptionType,
    InvoiceMatchStatus,
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
    SupplierInvoiceMatch,
)


MATCH_NOTE = "R5G HTTP postgres invoice match"
PO_NOTE = "R5G HTTP fixture PO"
SUPPLIER_NAME = "R5G HTTP Integration Supplier"
APPROVAL_COMMENT = "R5G HTTP invoice match approval"


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


def access_token(
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
            "exp": now + timedelta(minutes=15),
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
            + access_token(
                user_id=user_id,
                tenant_id=tenant_id,
                permissions=permissions,
            )
        ),
        "X-Tenant-ID": str(tenant_id),
    }


def submission_payload(
    *,
    match_id: UUID,
    requested_by: UUID,
    approver_id: UUID,
) -> dict:
    return {
        "object_type": "INVOICE_MATCH",
        "object_id": str(match_id),
        "requested_by": str(requested_by),
        "comments": APPROVAL_COMMENT,
        "steps": [
            {
                "step_number": 1,
                "approver_id": str(approver_id),
            }
        ],
    }


async def create_fixture(
    *,
    status: InvoiceMatchStatus = InvoiceMatchStatus.MATCHED,
):
    tenant_id = uuid4()
    requester_id = uuid4()
    now = datetime.now(UTC)

    supplier = ProcurementSupplier(
        id=uuid4(),
        tenant_id=tenant_id,
        supplier_code=f"R5G-{uuid4()}",
        legal_name=SUPPLIER_NAME,
        status=SupplierStatus.ACTIVE,
        created_by=requester_id,
        created_at=now,
        updated_at=now,
    )

    purchase_order = PurchaseOrder(
        id=uuid4(),
        tenant_id=tenant_id,
        po_number=f"R5G-PO-{uuid4()}",
        supplier_id=supplier.id,
        order_date=now.date(),
        currency_code="PKR",
        subtotal_amount=Decimal("1000.000000"),
        discount_amount=Decimal("0.000000"),
        tax_amount=Decimal("100.000000"),
        total_amount=Decimal("1100.000000"),
        notes=PO_NOTE,
        requested_by=requester_id,
        status=PurchaseOrderStatus.APPROVED,
        approved_by=requester_id,
        approved_at=now,
        created_at=now,
        updated_at=now,
    )

    invoice_match = SupplierInvoiceMatch(
        id=uuid4(),
        tenant_id=tenant_id,
        supplier_id=supplier.id,
        purchase_order_id=purchase_order.id,
        goods_receipt_id=None,
        supplier_invoice_number=f"R5G-INV-{uuid4()}",
        supplier_invoice_date=now.date(),
        currency_code="PKR",
        invoice_subtotal=Decimal("1000.000000"),
        invoice_tax_amount=Decimal("100.000000"),
        invoice_total=Decimal("1100.000000"),
        quantity_tolerance_percent=Decimal("0.000000"),
        price_tolerance_percent=Decimal("0.000000"),
        tax_tolerance_percent=Decimal("0.000000"),
        status=status,
        exception_type=InvoiceMatchExceptionType.NONE,
        matched_at=now,
        approved_by=None,
        approved_at=None,
        finance_ap_invoice_id=None,
        finance_handoff_at=None,
        dispute_reason=None,
        notes=MATCH_NOTE,
        created_at=now,
        updated_at=now,
    )

    async with AsyncSessionFactory() as session:
        session.add(supplier)
        session.add(purchase_order)
        session.add(invoice_match)
        await session.commit()

    return (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
        invoice_match,
    )


async def cleanup(
    *,
    match_id: UUID,
    purchase_order_id: UUID,
    supplier_id: UUID,
) -> None:
    async with AsyncSessionFactory() as session:
        approval_ids = (
            await session.scalars(
                select(ProcurementApprovalRequest.id).where(
                    ProcurementApprovalRequest.object_type
                    == ApprovalObjectType.INVOICE_MATCH,
                    ProcurementApprovalRequest.object_id
                    == match_id,
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
            delete(SupplierInvoiceMatch).where(
                SupplierInvoiceMatch.id == match_id
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


async def load_match(
    match_id: UUID,
) -> SupplierInvoiceMatch | None:
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(SupplierInvoiceMatch).where(
                SupplierInvoiceMatch.id == match_id
            )
        )


async def load_approval(
    match_id: UUID,
) -> ProcurementApprovalRequest | None:
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(ProcurementApprovalRequest).where(
                ProcurementApprovalRequest.object_type
                == ApprovalObjectType.INVOICE_MATCH,
                ProcurementApprovalRequest.object_id
                == match_id,
            )
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_http_submit_and_approve_persists_to_postgres():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
        invoice_match,
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
                    f"/invoice-matches/{invoice_match.id}"
                    "/submit-for-approval"
                ),
                headers=headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create",
                    ],
                ),
                json=submission_payload(
                    match_id=invoice_match.id,
                    requested_by=requester_id,
                    approver_id=approver_id,
                ),
            )

            assert submit.status_code == 201, submit.text
            assert submit.json()["status"] == "PENDING"

            approve = await client.post(
                (
                    f"/invoice-matches/{invoice_match.id}"
                    "/approval-steps/1/approve"
                ),
                headers=headers(
                    user_id=approver_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.approve",
                    ],
                ),
                json={
                    "decided_by": str(approver_id),
                    "comments": "R5G HTTP approved",
                },
            )

            assert approve.status_code == 200, approve.text
            assert approve.json()["status"] == "APPROVED"

        persisted_match = await load_match(
            invoice_match.id
        )
        persisted_approval = await load_approval(
            invoice_match.id
        )

        assert persisted_match is not None
        assert (
            persisted_match.status
            == InvoiceMatchStatus.APPROVED
        )
        assert persisted_match.approved_by == approver_id
        assert persisted_match.approved_at is not None

        assert persisted_approval is not None
        assert (
            persisted_approval.status
            == ApprovalRequestStatus.APPROVED
        )

    finally:
        await cleanup(
            match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_http_submit_and_reject_persists_to_postgres():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture(
        status=InvoiceMatchStatus.EXCEPTION
    )

    approver_id = uuid4()

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            submit = await client.post(
                (
                    f"/invoice-matches/{invoice_match.id}"
                    "/submit-for-approval"
                ),
                headers=headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create",
                    ],
                ),
                json=submission_payload(
                    match_id=invoice_match.id,
                    requested_by=requester_id,
                    approver_id=approver_id,
                ),
            )

            assert submit.status_code == 201, submit.text

            reject = await client.post(
                (
                    f"/invoice-matches/{invoice_match.id}"
                    "/approval-steps/1/reject"
                ),
                headers=headers(
                    user_id=approver_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.reject",
                    ],
                ),
                json={
                    "decided_by": str(approver_id),
                    "comments": "R5G HTTP rejected",
                },
            )

            assert reject.status_code == 200, reject.text
            assert reject.json()["status"] == "REJECTED"

        persisted_match = await load_match(
            invoice_match.id
        )
        persisted_approval = await load_approval(
            invoice_match.id
        )

        assert persisted_match is not None
        assert (
            persisted_match.status
            == InvoiceMatchStatus.REJECTED
        )
        assert persisted_match.approved_by is None
        assert persisted_match.approved_at is None
        assert (
            persisted_match.dispute_reason
            == "R5G HTTP rejected"
        )

        assert persisted_approval is not None
        assert (
            persisted_approval.status
            == ApprovalRequestStatus.REJECTED
        )

    finally:
        await cleanup(
            match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

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
from procurement_service.models import (
    ProcurementApprovalRequest,
    ProcurementApprovalStep,
    ProcurementSupplier,
    PurchaseOrder,
    SupplierInvoiceMatch,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.invoice_match_approval_coordinator import (
    DuplicateInvoiceMatchApprovalError,
    InvoiceMatchApprovalCoordinator,
    InvoiceMatchNotFoundError,
)


MATCH_NOTE = "R5E coordinator postgres invoice match"
PO_NOTE = "R5E coordinator fixture PO"
SUPPLIER_NAME = "R5E Coordinator Supplier"
APPROVAL_COMMENT = "R5E coordinator approval"


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


def make_supplier(
    *,
    tenant_id: UUID,
    actor_id: UUID,
) -> ProcurementSupplier:
    now = datetime.now(UTC)

    return ProcurementSupplier(
        id=uuid4(),
        tenant_id=tenant_id,
        supplier_code=f"R5E-{uuid4()}",
        legal_name=SUPPLIER_NAME,
        status=SupplierStatus.ACTIVE,
        created_by=actor_id,
        created_at=now,
        updated_at=now,
    )


def make_purchase_order(
    *,
    tenant_id: UUID,
    supplier_id: UUID,
    actor_id: UUID,
) -> PurchaseOrder:
    now = datetime.now(UTC)

    return PurchaseOrder(
        id=uuid4(),
        tenant_id=tenant_id,
        po_number=f"R5E-PO-{uuid4()}",
        supplier_id=supplier_id,
        order_date=now.date(),
        currency_code="PKR",
        subtotal_amount=Decimal("1000.000000"),
        discount_amount=Decimal("0.000000"),
        tax_amount=Decimal("100.000000"),
        total_amount=Decimal("1100.000000"),
        notes=PO_NOTE,
        requested_by=actor_id,
        status=PurchaseOrderStatus.APPROVED,
        approved_by=actor_id,
        approved_at=now,
        created_at=now,
        updated_at=now,
    )


def make_invoice_match(
    *,
    tenant_id: UUID,
    supplier_id: UUID,
    purchase_order_id: UUID,
    status: InvoiceMatchStatus = InvoiceMatchStatus.MATCHED,
) -> SupplierInvoiceMatch:
    now = datetime.now(UTC)

    return SupplierInvoiceMatch(
        id=uuid4(),
        tenant_id=tenant_id,
        supplier_id=supplier_id,
        purchase_order_id=purchase_order_id,
        goods_receipt_id=None,
        supplier_invoice_number=f"R5E-INV-{uuid4()}",
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


def make_payload(
    *,
    invoice_match: SupplierInvoiceMatch,
    requester_id: UUID,
    approver_id: UUID,
) -> ProcurementApprovalRequestCreate:
    return ProcurementApprovalRequestCreate(
        object_type=ApprovalObjectType.INVOICE_MATCH,
        object_id=invoice_match.id,
        requested_by=requester_id,
        comments=APPROVAL_COMMENT,
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
                approver_id=approver_id,
            )
        ],
    )


async def create_fixture(
    *,
    status: InvoiceMatchStatus = InvoiceMatchStatus.MATCHED,
):
    tenant_id = uuid4()
    requester_id = uuid4()

    supplier = make_supplier(
        tenant_id=tenant_id,
        actor_id=requester_id,
    )

    purchase_order = make_purchase_order(
        tenant_id=tenant_id,
        supplier_id=supplier.id,
        actor_id=requester_id,
    )

    invoice_match = make_invoice_match(
        tenant_id=tenant_id,
        supplier_id=supplier.id,
        purchase_order_id=purchase_order.id,
        status=status,
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
    invoice_match_id: UUID,
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
                    == invoice_match_id,
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
                SupplierInvoiceMatch.id == invoice_match_id
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
    invoice_match_id: UUID,
) -> SupplierInvoiceMatch | None:
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(SupplierInvoiceMatch).where(
                SupplierInvoiceMatch.id == invoice_match_id
            )
        )


async def load_approval(
    invoice_match_id: UUID,
) -> ProcurementApprovalRequest | None:
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(ProcurementApprovalRequest).where(
                ProcurementApprovalRequest.object_type
                == ApprovalObjectType.INVOICE_MATCH,
                ProcurementApprovalRequest.object_id
                == invoice_match_id,
            )
        )


async def approval_count(
    invoice_match_id: UUID,
) -> int:
    async with AsyncSessionFactory() as session:
        ids = (
            await session.scalars(
                select(ProcurementApprovalRequest.id).where(
                    ProcurementApprovalRequest.object_type
                    == ApprovalObjectType.INVOICE_MATCH,
                    ProcurementApprovalRequest.object_id
                    == invoice_match_id,
                )
            )
        ).all()

        return len(ids)


@pytest.mark.asyncio(loop_scope="module")
async def test_submit_then_approve_persists_terminal_state():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            loaded_match, approval = (
                await coordinator.submit_for_approval(
                    tenant_id=tenant_id,
                    invoice_match_id=invoice_match.id,
                    payload=make_payload(
                        invoice_match=invoice_match,
                        requester_id=requester_id,
                        approver_id=approver_id,
                    ),
                )
            )

            await session.commit()

            assert loaded_match.id == invoice_match.id
            assert approval.status == ApprovalRequestStatus.PENDING

        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            loaded_match, approval = (
                await coordinator.approve_step(
                    tenant_id=tenant_id,
                    invoice_match_id=invoice_match.id,
                    step_number=1,
                    decision=ProcurementApprovalStepDecision(
                        decided_by=approver_id,
                        comments="R5E approved",
                    ),
                )
            )

            await session.commit()

            assert approval.status == ApprovalRequestStatus.APPROVED
            assert loaded_match.status == InvoiceMatchStatus.APPROVED

        persisted = await load_match(invoice_match.id)
        approval = await load_approval(invoice_match.id)

        assert persisted is not None
        assert persisted.status == InvoiceMatchStatus.APPROVED
        assert persisted.approved_by == approver_id
        assert persisted.approved_at is not None

        assert approval is not None
        assert approval.status == ApprovalRequestStatus.APPROVED

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_submit_then_reject_persists_rejected_state():
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
        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                invoice_match_id=invoice_match.id,
                payload=make_payload(
                    invoice_match=invoice_match,
                    requester_id=requester_id,
                    approver_id=approver_id,
                ),
            )

            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            loaded_match, approval = (
                await coordinator.reject_step(
                    tenant_id=tenant_id,
                    invoice_match_id=invoice_match.id,
                    step_number=1,
                    decision=ProcurementApprovalStepDecision(
                        decided_by=approver_id,
                        comments="R5E rejected",
                    ),
                )
            )

            await session.commit()

            assert approval.status == ApprovalRequestStatus.REJECTED
            assert loaded_match.status == InvoiceMatchStatus.REJECTED

        persisted = await load_match(invoice_match.id)

        assert persisted is not None
        assert persisted.status == InvoiceMatchStatus.REJECTED
        assert persisted.approved_by is None
        assert persisted.approved_at is None
        assert persisted.dispute_reason == "R5E rejected"

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_duplicate_submission_is_rejected():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                invoice_match_id=invoice_match.id,
                payload=make_payload(
                    invoice_match=invoice_match,
                    requester_id=requester_id,
                    approver_id=approver_id,
                ),
            )

            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            with pytest.raises(
                DuplicateInvoiceMatchApprovalError
            ):
                await coordinator.submit_for_approval(
                    tenant_id=tenant_id,
                    invoice_match_id=invoice_match.id,
                    payload=make_payload(
                        invoice_match=invoice_match,
                        requester_id=requester_id,
                        approver_id=approver_id,
                    ),
                )

            await session.rollback()

        assert await approval_count(invoice_match.id) == 1

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_concurrent_submission_creates_single_approval():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    approver_id = uuid4()

    async def submit_once():
        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            try:
                await coordinator.submit_for_approval(
                    tenant_id=tenant_id,
                    invoice_match_id=invoice_match.id,
                    payload=make_payload(
                        invoice_match=invoice_match,
                        requester_id=requester_id,
                        approver_id=approver_id,
                    ),
                )

                await session.commit()
                return "committed"

            except (
                DuplicateInvoiceMatchApprovalError,
                IntegrityError,
            ):
                await session.rollback()
                return "rejected"

    try:
        results = await asyncio.gather(
            submit_once(),
            submit_once(),
        )

        assert results.count("committed") == 1
        assert results.count("rejected") == 1
        assert await approval_count(invoice_match.id) == 1

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_cross_tenant_submit_cannot_load_match():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            with pytest.raises(InvoiceMatchNotFoundError):
                await coordinator.submit_for_approval(
                    tenant_id=uuid4(),
                    invoice_match_id=invoice_match.id,
                    payload=make_payload(
                        invoice_match=invoice_match,
                        requester_id=requester_id,
                        approver_id=uuid4(),
                    ),
                )

            await session.rollback()

        assert await approval_count(invoice_match.id) == 0

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_submission_rollback_leaves_no_approval():
    (
        tenant_id,
        requester_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = InvoiceMatchApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                invoice_match_id=invoice_match.id,
                payload=make_payload(
                    invoice_match=invoice_match,
                    requester_id=requester_id,
                    approver_id=uuid4(),
                ),
            )

            await session.rollback()

        persisted = await load_match(invoice_match.id)

        assert persisted is not None
        assert persisted.status == InvoiceMatchStatus.MATCHED
        assert persisted.approved_by is None
        assert persisted.approved_at is None

        assert await approval_count(invoice_match.id) == 0

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )

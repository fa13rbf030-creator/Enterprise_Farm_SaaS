from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

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
    ProcurementSupplier,
    PurchaseOrder,
    SupplierInvoiceMatch,
)
from procurement_service.repositories.invoice_match import (
    SupplierInvoiceMatchRepository,
)
from procurement_service.services.invoice_match_approval import (
    InvoiceMatchApprovalIntegrationService,
)


MATCH_NOTE = "R5C postgres invoice match approval"
PO_NOTE = "R5C postgres fixture PO"
SUPPLIER_NAME = "R5C Integration Supplier"


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
    created_by: UUID,
) -> ProcurementSupplier:
    now = datetime.now(UTC)

    return ProcurementSupplier(
        id=uuid4(),
        tenant_id=tenant_id,
        supplier_code=f"R5C-{uuid4()}",
        legal_name=SUPPLIER_NAME,
        status=SupplierStatus.ACTIVE,
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )


def make_purchase_order(
    *,
    tenant_id: UUID,
    supplier_id: UUID,
    requested_by: UUID,
) -> PurchaseOrder:
    now = datetime.now(UTC)

    return PurchaseOrder(
        id=uuid4(),
        tenant_id=tenant_id,
        po_number=f"R5C-PO-{uuid4()}",
        supplier_id=supplier_id,
        order_date=now.date(),
        currency_code="PKR",
        subtotal_amount=Decimal("1000.000000"),
        discount_amount=Decimal("0.000000"),
        tax_amount=Decimal("100.000000"),
        total_amount=Decimal("1100.000000"),
        notes=PO_NOTE,
        requested_by=requested_by,
        status=PurchaseOrderStatus.APPROVED,
        approved_by=requested_by,
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
        supplier_invoice_number=f"R5C-INV-{uuid4()}",
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


def make_approval(
    *,
    invoice_match: SupplierInvoiceMatch,
    status: ApprovalRequestStatus,
) -> ProcurementApprovalRequest:
    now = datetime.now(UTC)

    return ProcurementApprovalRequest(
        id=uuid4(),
        tenant_id=invoice_match.tenant_id,
        object_type=ApprovalObjectType.INVOICE_MATCH,
        object_id=invoice_match.id,
        status=status,
        requested_by=uuid4(),
        requested_at=now,
        completed_at=(
            now
            if status
            in {
                ApprovalRequestStatus.APPROVED,
                ApprovalRequestStatus.REJECTED,
            }
            else None
        ),
        current_step=1,
        total_steps=1,
        comments="R5C synthetic approval",
        created_at=now,
        updated_at=now,
    )


async def create_fixture(
    *,
    status: InvoiceMatchStatus = InvoiceMatchStatus.MATCHED,
):
    tenant_id = uuid4()
    actor_id = uuid4()

    supplier = make_supplier(
        tenant_id=tenant_id,
        created_by=actor_id,
    )

    purchase_order = make_purchase_order(
        tenant_id=tenant_id,
        supplier_id=supplier.id,
        requested_by=actor_id,
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
        actor_id,
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
        await session.execute(
            delete(ProcurementApprovalRequest).where(
                ProcurementApprovalRequest.object_type
                == ApprovalObjectType.INVOICE_MATCH,
                ProcurementApprovalRequest.object_id
                == invoice_match_id,
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


@pytest.mark.asyncio(loop_scope="module")
async def test_repository_loads_match_with_tenant_scope_and_lock():
    (
        tenant_id,
        actor_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    try:
        async with AsyncSessionFactory() as session:
            repository = SupplierInvoiceMatchRepository(
                session
            )

            loaded = await repository.get_by_id(
                tenant_id=tenant_id,
                invoice_match_id=invoice_match.id,
                for_update=True,
            )

            assert loaded is not None
            assert loaded.id == invoice_match.id
            assert loaded.tenant_id == tenant_id

            await session.rollback()

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_cross_tenant_repository_lookup_returns_none():
    (
        tenant_id,
        actor_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    try:
        async with AsyncSessionFactory() as session:
            repository = SupplierInvoiceMatchRepository(
                session
            )

            loaded = await repository.get_by_id(
                tenant_id=uuid4(),
                invoice_match_id=invoice_match.id,
                for_update=True,
            )

            assert loaded is None

            await session.rollback()

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_approved_outcome_persists_to_postgres():
    (
        tenant_id,
        actor_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        async with AsyncSessionFactory() as session:
            repository = SupplierInvoiceMatchRepository(
                session
            )

            loaded = await repository.get_by_id(
                tenant_id=tenant_id,
                invoice_match_id=invoice_match.id,
                for_update=True,
            )

            assert loaded is not None

            approval = make_approval(
                invoice_match=loaded,
                status=ApprovalRequestStatus.APPROVED,
            )

            InvoiceMatchApprovalIntegrationService.submit(
                loaded
            )

            InvoiceMatchApprovalIntegrationService.synchronize_outcome(
                invoice_match=loaded,
                approval=approval,
                decided_by=approver_id,
            )

            await repository.flush()
            await session.commit()

        persisted = await load_match(invoice_match.id)

        assert persisted is not None
        assert persisted.status == InvoiceMatchStatus.APPROVED
        assert persisted.approved_by == approver_id
        assert persisted.approved_at is not None
        assert persisted.dispute_reason is None

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_rejected_outcome_persists_to_postgres():
    (
        tenant_id,
        actor_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture(
        status=InvoiceMatchStatus.EXCEPTION
    )

    approver_id = uuid4()

    try:
        async with AsyncSessionFactory() as session:
            repository = SupplierInvoiceMatchRepository(
                session
            )

            loaded = await repository.get_by_id(
                tenant_id=tenant_id,
                invoice_match_id=invoice_match.id,
                for_update=True,
            )

            assert loaded is not None

            approval = make_approval(
                invoice_match=loaded,
                status=ApprovalRequestStatus.REJECTED,
            )

            InvoiceMatchApprovalIntegrationService.submit(
                loaded
            )

            InvoiceMatchApprovalIntegrationService.synchronize_outcome(
                invoice_match=loaded,
                approval=approval,
                decided_by=approver_id,
                rejection_reason="R5C tolerance exception rejected",
            )

            await repository.flush()
            await session.commit()

        persisted = await load_match(invoice_match.id)

        assert persisted is not None
        assert persisted.status == InvoiceMatchStatus.REJECTED
        assert persisted.approved_by is None
        assert persisted.approved_at is None
        assert (
            persisted.dispute_reason
            == "R5C tolerance exception rejected"
        )

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_rollback_preserves_original_match_state():
    (
        tenant_id,
        actor_id,
        supplier,
        purchase_order,
        invoice_match,
    ) = await create_fixture()

    try:
        async with AsyncSessionFactory() as session:
            repository = SupplierInvoiceMatchRepository(
                session
            )

            loaded = await repository.get_by_id(
                tenant_id=tenant_id,
                invoice_match_id=invoice_match.id,
                for_update=True,
            )

            assert loaded is not None

            approval = make_approval(
                invoice_match=loaded,
                status=ApprovalRequestStatus.APPROVED,
            )

            InvoiceMatchApprovalIntegrationService.synchronize_outcome(
                invoice_match=loaded,
                approval=approval,
                decided_by=uuid4(),
            )

            await session.rollback()

        persisted = await load_match(invoice_match.id)

        assert persisted is not None
        assert persisted.status == InvoiceMatchStatus.MATCHED
        assert persisted.approved_by is None
        assert persisted.approved_at is None

    finally:
        await cleanup(
            invoice_match_id=invoice_match.id,
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )

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
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.purchase_order_approval_coordinator import (
    DuplicatePurchaseOrderApprovalError,
    PurchaseOrderApprovalCoordinator,
    PurchaseOrderNotFoundError,
)


PO_NOTE = "R4D postgres approval integration"
APPROVAL_COMMENT = "R4D purchase order approval"
SUPPLIER_NAME = "R4D Integration Supplier"


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
        supplier_code=f"R4D-{uuid4()}",
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
        po_number=f"R4D-PO-{uuid4()}",
        supplier_id=supplier_id,
        order_date=now.date(),
        currency_code="USD",
        subtotal_amount=Decimal("100.000000"),
        discount_amount=Decimal("0.000000"),
        tax_amount=Decimal("10.000000"),
        total_amount=Decimal("110.000000"),
        notes=PO_NOTE,
        requested_by=requested_by,
        status=PurchaseOrderStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )


def make_payload(
    *,
    purchase_order: PurchaseOrder,
    approver_id: UUID,
) -> ProcurementApprovalRequestCreate:
    return ProcurementApprovalRequestCreate(
        object_type=ApprovalObjectType.PURCHASE_ORDER,
        object_id=purchase_order.id,
        requested_by=purchase_order.requested_by,
        comments=APPROVAL_COMMENT,
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
                approver_id=approver_id,
            )
        ],
    )


async def create_fixture():
    tenant_id = uuid4()
    requested_by = uuid4()

    supplier = make_supplier(
        tenant_id=tenant_id,
        created_by=requested_by,
    )

    purchase_order = make_purchase_order(
        tenant_id=tenant_id,
        supplier_id=supplier.id,
        requested_by=requested_by,
    )

    async with AsyncSessionFactory() as session:
        session.add(supplier)
        session.add(purchase_order)
        await session.commit()

    return tenant_id, requested_by, supplier, purchase_order


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


async def approval_count(
    purchase_order_id: UUID,
) -> int:
    async with AsyncSessionFactory() as session:
        values = (
            await session.scalars(
                select(ProcurementApprovalRequest.id).where(
                    ProcurementApprovalRequest.object_type
                    == ApprovalObjectType.PURCHASE_ORDER,
                    ProcurementApprovalRequest.object_id
                    == purchase_order_id,
                )
            )
        ).all()

        return len(values)


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


@pytest.mark.asyncio(loop_scope="module")
async def test_submit_and_final_approval_persist_business_state():
    (
        tenant_id,
        requested_by,
        supplier,
        purchase_order,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            persisted_po, approval = (
                await coordinator.submit_for_approval(
                    tenant_id=tenant_id,
                    purchase_order_id=purchase_order.id,
                    payload=make_payload(
                        purchase_order=purchase_order,
                        approver_id=approver_id,
                    ),
                )
            )

            await session.commit()

            assert (
                persisted_po.status
                == PurchaseOrderStatus.PENDING_APPROVAL
            )
            assert (
                approval.status
                == ApprovalRequestStatus.PENDING
            )

        submitted = await load_purchase_order(
            purchase_order.id
        )

        assert submitted is not None
        assert (
            submitted.status
            == PurchaseOrderStatus.PENDING_APPROVAL
        )

        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            persisted_po, approval = (
                await coordinator.approve_step(
                    tenant_id=tenant_id,
                    purchase_order_id=purchase_order.id,
                    step_number=1,
                    decision=ProcurementApprovalStepDecision(
                        decided_by=approver_id,
                        comments="R4D approved",
                    ),
                )
            )

            await session.commit()

            assert (
                approval.status
                == ApprovalRequestStatus.APPROVED
            )
            assert (
                persisted_po.status
                == PurchaseOrderStatus.APPROVED
            )

        persisted = await load_purchase_order(
            purchase_order.id
        )

        assert persisted is not None
        assert persisted.status == PurchaseOrderStatus.APPROVED
        assert persisted.approved_by == approver_id
        assert persisted.approved_at is not None

        approval = await load_approval(purchase_order.id)

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
async def test_rejection_returns_purchase_order_to_draft():
    (
        tenant_id,
        requested_by,
        supplier,
        purchase_order,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                purchase_order_id=purchase_order.id,
                payload=make_payload(
                    purchase_order=purchase_order,
                    approver_id=approver_id,
                ),
            )

            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            persisted_po, approval = (
                await coordinator.reject_step(
                    tenant_id=tenant_id,
                    purchase_order_id=purchase_order.id,
                    step_number=1,
                    decision=ProcurementApprovalStepDecision(
                        decided_by=approver_id,
                        comments="R4D rejected",
                    ),
                )
            )

            await session.commit()

            assert (
                approval.status
                == ApprovalRequestStatus.REJECTED
            )
            assert (
                persisted_po.status
                == PurchaseOrderStatus.DRAFT
            )

        persisted = await load_purchase_order(
            purchase_order.id
        )

        assert persisted is not None
        assert persisted.status == PurchaseOrderStatus.DRAFT
        assert persisted.approved_by is None
        assert persisted.approved_at is None

    finally:
        await cleanup(
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_duplicate_submission_is_rejected():
    (
        tenant_id,
        requested_by,
        supplier,
        purchase_order,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                purchase_order_id=purchase_order.id,
                payload=make_payload(
                    purchase_order=purchase_order,
                    approver_id=approver_id,
                ),
            )

            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            with pytest.raises(
                DuplicatePurchaseOrderApprovalError
            ):
                await coordinator.submit_for_approval(
                    tenant_id=tenant_id,
                    purchase_order_id=purchase_order.id,
                    payload=make_payload(
                        purchase_order=purchase_order,
                        approver_id=approver_id,
                    ),
                )

            await session.rollback()

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


@pytest.mark.asyncio(loop_scope="module")
async def test_concurrent_submission_creates_only_one_approval():
    (
        tenant_id,
        requested_by,
        supplier,
        purchase_order,
    ) = await create_fixture()

    approver_id = uuid4()

    async def submit_once():
        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            try:
                await coordinator.submit_for_approval(
                    tenant_id=tenant_id,
                    purchase_order_id=purchase_order.id,
                    payload=make_payload(
                        purchase_order=purchase_order,
                        approver_id=approver_id,
                    ),
                )

                await session.commit()
                return "committed"

            except (
                DuplicatePurchaseOrderApprovalError,
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


@pytest.mark.asyncio(loop_scope="module")
async def test_submission_rollback_preserves_draft():
    (
        tenant_id,
        requested_by,
        supplier,
        purchase_order,
    ) = await create_fixture()

    approver_id = uuid4()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                purchase_order_id=purchase_order.id,
                payload=make_payload(
                    purchase_order=purchase_order,
                    approver_id=approver_id,
                ),
            )

            await session.rollback()

        persisted = await load_purchase_order(
            purchase_order.id
        )

        assert persisted is not None
        assert persisted.status == PurchaseOrderStatus.DRAFT
        assert await approval_count(purchase_order.id) == 0

    finally:
        await cleanup(
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_cross_tenant_submission_cannot_load_purchase_order():
    (
        tenant_id,
        requested_by,
        supplier,
        purchase_order,
    ) = await create_fixture()

    try:
        async with AsyncSessionFactory() as session:
            coordinator = PurchaseOrderApprovalCoordinator(
                session
            )

            with pytest.raises(PurchaseOrderNotFoundError):
                await coordinator.submit_for_approval(
                    tenant_id=uuid4(),
                    purchase_order_id=purchase_order.id,
                    payload=make_payload(
                        purchase_order=purchase_order,
                        approver_id=uuid4(),
                    ),
                )

            await session.rollback()

        persisted = await load_purchase_order(
            purchase_order.id
        )

        assert persisted is not None
        assert persisted.status == PurchaseOrderStatus.DRAFT
        assert await approval_count(purchase_order.id) == 0

    finally:
        await cleanup(
            purchase_order_id=purchase_order.id,
            supplier_id=supplier.id,
        )

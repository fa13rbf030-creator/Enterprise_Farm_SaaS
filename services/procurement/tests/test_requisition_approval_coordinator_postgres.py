import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    RequisitionStatus,
)
from procurement_service.db.session import (
    AsyncSessionFactory,
    engine,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
    ProcurementApprovalStep,
    PurchaseRequisition,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.requisition_approval_coordinator import (
    DuplicateRequisitionApprovalError,
    RequisitionApprovalCoordinator,
)


PURPOSE = "R3D-B coordinator postgres test"
APPROVAL_COMMENT = "R3D-B coordinator approval"


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


def make_requisition(
    *,
    tenant_id: UUID,
    requester_id: UUID,
) -> PurchaseRequisition:
    now = datetime.now(UTC)

    return PurchaseRequisition(
        id=uuid4(),
        tenant_id=tenant_id,
        requisition_number=f"R3DB-{uuid4()}",
        requester_id=requester_id,
        purpose=PURPOSE,
        status=RequisitionStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )


def make_payload(
    *,
    requisition: PurchaseRequisition,
    approver_id: UUID,
) -> ProcurementApprovalRequestCreate:
    return ProcurementApprovalRequestCreate(
        object_type=ApprovalObjectType.PURCHASE_REQUISITION,
        object_id=requisition.id,
        requested_by=requisition.requester_id,
        comments=APPROVAL_COMMENT,
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
                approver_id=approver_id,
            )
        ],
    )


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


async def load_approval_count(
    requisition_id: UUID,
) -> int:
    async with AsyncSessionFactory() as session:
        values = (
            await session.scalars(
                select(ProcurementApprovalRequest.id).where(
                    ProcurementApprovalRequest.object_type
                    == ApprovalObjectType.PURCHASE_REQUISITION,
                    ProcurementApprovalRequest.object_id
                    == requisition_id,
                )
            )
        ).all()

        return len(values)


@pytest.mark.asyncio(loop_scope="module")
async def test_duplicate_submission_is_rejected():
    tenant_id = uuid4()
    requester_id = uuid4()
    approver_id = uuid4()

    requisition = make_requisition(
        tenant_id=tenant_id,
        requester_id=requester_id,
    )

    requisition_id = requisition.id

    try:
        async with AsyncSessionFactory() as session:
            session.add(requisition)
            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = RequisitionApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                payload=make_payload(
                    requisition=requisition,
                    approver_id=approver_id,
                ),
            )

            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = RequisitionApprovalCoordinator(
                session
            )

            with pytest.raises(
                DuplicateRequisitionApprovalError
            ):
                await coordinator.submit_for_approval(
                    tenant_id=tenant_id,
                    requisition_id=requisition_id,
                    payload=make_payload(
                        requisition=requisition,
                        approver_id=approver_id,
                    ),
                )

            await session.rollback()

        assert await load_approval_count(requisition_id) == 1

        persisted = await load_requisition(requisition_id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.SUBMITTED

    finally:
        await cleanup(requisition_id)


@pytest.mark.asyncio(loop_scope="module")
async def test_concurrent_submission_never_creates_two_approvals():
    tenant_id = uuid4()
    requester_id = uuid4()
    approver_id = uuid4()

    requisition = make_requisition(
        tenant_id=tenant_id,
        requester_id=requester_id,
    )

    requisition_id = requisition.id

    async with AsyncSessionFactory() as session:
        session.add(requisition)
        await session.commit()

    async def submit_once():
        async with AsyncSessionFactory() as session:
            coordinator = RequisitionApprovalCoordinator(
                session
            )

            try:
                await coordinator.submit_for_approval(
                    tenant_id=tenant_id,
                    requisition_id=requisition_id,
                    payload=make_payload(
                        requisition=requisition,
                        approver_id=approver_id,
                    ),
                )

                await session.commit()

                return "committed"

            except (
                DuplicateRequisitionApprovalError,
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

        assert await load_approval_count(requisition_id) == 1

        persisted = await load_requisition(requisition_id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.SUBMITTED

    finally:
        await cleanup(requisition_id)


@pytest.mark.asyncio(loop_scope="module")
async def test_submit_rollback_preserves_draft_and_no_approval():
    tenant_id = uuid4()
    requester_id = uuid4()
    approver_id = uuid4()

    requisition = make_requisition(
        tenant_id=tenant_id,
        requester_id=requester_id,
    )

    requisition_id = requisition.id

    try:
        async with AsyncSessionFactory() as session:
            session.add(requisition)
            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = RequisitionApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                payload=make_payload(
                    requisition=requisition,
                    approver_id=approver_id,
                ),
            )

            await session.rollback()

        persisted = await load_requisition(requisition_id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.DRAFT

        assert await load_approval_count(requisition_id) == 0

    finally:
        await cleanup(requisition_id)


@pytest.mark.asyncio(loop_scope="module")
async def test_coordinator_final_approval_persists_business_state():
    tenant_id = uuid4()
    requester_id = uuid4()
    approver_id = uuid4()

    requisition = make_requisition(
        tenant_id=tenant_id,
        requester_id=requester_id,
    )

    requisition_id = requisition.id

    try:
        async with AsyncSessionFactory() as session:
            session.add(requisition)
            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = RequisitionApprovalCoordinator(
                session
            )

            await coordinator.submit_for_approval(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                payload=make_payload(
                    requisition=requisition,
                    approver_id=approver_id,
                ),
            )

            await session.commit()

        async with AsyncSessionFactory() as session:
            coordinator = RequisitionApprovalCoordinator(
                session
            )

            persisted_requisition, approval = (
                await coordinator.approve_step(
                    tenant_id=tenant_id,
                    requisition_id=requisition_id,
                    step_number=1,
                    decision=ProcurementApprovalStepDecision(
                        decided_by=approver_id,
                        comments="approved via coordinator",
                    ),
                )
            )

            await session.commit()

            assert (
                approval.status
                == ApprovalRequestStatus.APPROVED
            )

            assert (
                persisted_requisition.status
                == RequisitionStatus.APPROVED
            )

        persisted = await load_requisition(requisition_id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.APPROVED
        assert persisted.approved_by == approver_id
        assert persisted.approved_at is not None

    finally:
        await cleanup(requisition_id)

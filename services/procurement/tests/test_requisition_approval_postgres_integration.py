from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

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
from procurement_service.repositories.approval import (
    ProcurementApprovalRepository,
)
from procurement_service.repositories.requisition import (
    PurchaseRequisitionRepository,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
    ProcurementApprovalStepDecision,
)
from procurement_service.services.approval import (
    ApprovalWorkflowService,
)
from procurement_service.services.requisition_approval import (
    RequisitionApprovalIntegrationService,
)


PURPOSE = "R3C postgres approval integration"
APPROVAL_COMMENT = "R3C requisition approval"


@pytest_asyncio.fixture(
    scope="module",
    loop_scope="module",
    autouse=True,
)
async def isolate_async_engine_pool():
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
        requisition_number=f"R3C-{uuid4()}",
        requester_id=requester_id,
        purpose=PURPOSE,
        status=RequisitionStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )


def make_approval_payload(
    *,
    requisition: PurchaseRequisition,
    requester_id: UUID,
    approver_id: UUID,
) -> ProcurementApprovalRequestCreate:
    return ProcurementApprovalRequestCreate(
        object_type=ApprovalObjectType.PURCHASE_REQUISITION,
        object_id=requisition.id,
        requested_by=requester_id,
        comments=APPROVAL_COMMENT,
        steps=[
            ProcurementApprovalStepCreate(
                step_number=1,
                approver_id=approver_id,
            )
        ],
    )


async def cleanup(
    *,
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
) -> PurchaseRequisition | None:
    async with AsyncSessionFactory() as session:
        return await session.scalar(
            select(PurchaseRequisition).where(
                PurchaseRequisition.id == requisition_id
            )
        )


async def load_approval(
    requisition_id: UUID,
) -> ProcurementApprovalRequest | None:
    async with AsyncSessionFactory() as session:
        repository = ProcurementApprovalRepository(session)

        result = await session.scalar(
            select(PurchaseRequisition).where(
                PurchaseRequisition.id == requisition_id
            )
        )

        if result is None:
            return None

        return await repository.get_by_object(
            tenant_id=result.tenant_id,
            object_type=ApprovalObjectType.PURCHASE_REQUISITION,
            object_id=requisition_id,
        )


@pytest.mark.asyncio(loop_scope="module")
async def test_submit_and_create_approval_commit_atomically():
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
            requisition_repository = (
                PurchaseRequisitionRepository(session)
            )
            approval_repository = (
                ProcurementApprovalRepository(session)
            )

            session.add(requisition)
            await session.flush()

            loaded = await requisition_repository.get_by_id(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                for_update=True,
            )

            assert loaded is not None

            RequisitionApprovalIntegrationService.submit(
                requisition=loaded
            )

            approval = ApprovalWorkflowService.create_request(
                tenant_id=tenant_id,
                payload=make_approval_payload(
                    requisition=loaded,
                    requester_id=requester_id,
                    approver_id=approver_id,
                ),
            )

            await approval_repository.add(approval)
            await requisition_repository.flush()

            await session.commit()

        persisted = await load_requisition(requisition_id)
        persisted_approval = await load_approval(requisition_id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.SUBMITTED
        assert persisted.submitted_at is not None

        assert persisted_approval is not None
        assert (
            persisted_approval.object_type
            == ApprovalObjectType.PURCHASE_REQUISITION
        )
        assert persisted_approval.object_id == requisition_id
        assert (
            persisted_approval.status
            == ApprovalRequestStatus.PENDING
        )

    finally:
        await cleanup(requisition_id=requisition_id)


@pytest.mark.asyncio(loop_scope="module")
async def test_final_approval_updates_requisition_same_transaction():
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
            requisition_repository = (
                PurchaseRequisitionRepository(session)
            )
            approval_repository = (
                ProcurementApprovalRepository(session)
            )

            session.add(requisition)
            await session.flush()

            loaded = await requisition_repository.get_by_id(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                for_update=True,
            )

            assert loaded is not None

            RequisitionApprovalIntegrationService.submit(
                requisition=loaded
            )

            approval = ApprovalWorkflowService.create_request(
                tenant_id=tenant_id,
                payload=make_approval_payload(
                    requisition=loaded,
                    requester_id=requester_id,
                    approver_id=approver_id,
                ),
            )

            await approval_repository.add(approval)
            await session.commit()

        async with AsyncSessionFactory() as session:
            requisition_repository = (
                PurchaseRequisitionRepository(session)
            )
            approval_repository = (
                ProcurementApprovalRepository(session)
            )

            locked_requisition = (
                await requisition_repository.get_by_id(
                    tenant_id=tenant_id,
                    requisition_id=requisition_id,
                    for_update=True,
                )
            )

            locked_approval = (
                await approval_repository.get_by_object(
                    tenant_id=tenant_id,
                    object_type=(
                        ApprovalObjectType.PURCHASE_REQUISITION
                    ),
                    object_id=requisition_id,
                    for_update=True,
                )
            )

            assert locked_requisition is not None
            assert locked_approval is not None

            ApprovalWorkflowService.approve_step(
                request=locked_approval,
                step_number=1,
                decision=ProcurementApprovalStepDecision(
                    decided_by=approver_id,
                    comments="R3C approved",
                ),
            )

            assert (
                locked_approval.status
                == ApprovalRequestStatus.APPROVED
            )

            RequisitionApprovalIntegrationService.synchronize_terminal_approval(
                requisition=locked_requisition,
                approval_request=locked_approval,
                decided_by=approver_id,
            )

            await approval_repository.flush()
            await requisition_repository.flush()
            await session.commit()

        persisted = await load_requisition(requisition_id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.APPROVED
        assert persisted.approved_by == approver_id
        assert persisted.approved_at is not None
        assert persisted.rejection_reason is None

        persisted_approval = await load_approval(requisition_id)

        assert persisted_approval is not None
        assert (
            persisted_approval.status
            == ApprovalRequestStatus.APPROVED
        )

    finally:
        await cleanup(requisition_id=requisition_id)


@pytest.mark.asyncio(loop_scope="module")
async def test_rejection_updates_requisition_same_transaction():
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
            requisition_repository = (
                PurchaseRequisitionRepository(session)
            )
            approval_repository = (
                ProcurementApprovalRepository(session)
            )

            session.add(requisition)
            await session.flush()

            loaded = await requisition_repository.get_by_id(
                tenant_id=tenant_id,
                requisition_id=requisition_id,
                for_update=True,
            )

            assert loaded is not None

            RequisitionApprovalIntegrationService.submit(
                requisition=loaded
            )

            approval = ApprovalWorkflowService.create_request(
                tenant_id=tenant_id,
                payload=make_approval_payload(
                    requisition=loaded,
                    requester_id=requester_id,
                    approver_id=approver_id,
                ),
            )

            await approval_repository.add(approval)
            await session.commit()

        async with AsyncSessionFactory() as session:
            requisition_repository = (
                PurchaseRequisitionRepository(session)
            )
            approval_repository = (
                ProcurementApprovalRepository(session)
            )

            locked_requisition = (
                await requisition_repository.get_by_id(
                    tenant_id=tenant_id,
                    requisition_id=requisition_id,
                    for_update=True,
                )
            )

            locked_approval = (
                await approval_repository.get_by_object(
                    tenant_id=tenant_id,
                    object_type=(
                        ApprovalObjectType.PURCHASE_REQUISITION
                    ),
                    object_id=requisition_id,
                    for_update=True,
                )
            )

            assert locked_requisition is not None
            assert locked_approval is not None

            ApprovalWorkflowService.reject_step(
                request=locked_approval,
                step_number=1,
                decision=ProcurementApprovalStepDecision(
                    decided_by=approver_id,
                    comments="Budget rejected",
                ),
            )

            RequisitionApprovalIntegrationService.synchronize_terminal_approval(
                requisition=locked_requisition,
                approval_request=locked_approval,
                rejection_reason="Budget rejected",
            )

            await approval_repository.flush()
            await requisition_repository.flush()
            await session.commit()

        persisted = await load_requisition(requisition_id)

        assert persisted is not None
        assert persisted.status == RequisitionStatus.REJECTED
        assert persisted.approved_by is None
        assert persisted.approved_at is None
        assert persisted.rejection_reason == "Budget rejected"

        persisted_approval = await load_approval(requisition_id)

        assert persisted_approval is not None
        assert (
            persisted_approval.status
            == ApprovalRequestStatus.REJECTED
        )

    finally:
        await cleanup(requisition_id=requisition_id)


@pytest.mark.asyncio(loop_scope="module")
async def test_transaction_rollback_does_not_persist_partial_workflow():
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
            approval_repository = (
                ProcurementApprovalRepository(session)
            )

            session.add(requisition)
            await session.flush()

            RequisitionApprovalIntegrationService.submit(
                requisition=requisition
            )

            approval = ApprovalWorkflowService.create_request(
                tenant_id=tenant_id,
                payload=make_approval_payload(
                    requisition=requisition,
                    requester_id=requester_id,
                    approver_id=approver_id,
                ),
            )

            await approval_repository.add(approval)

            await session.rollback()

        assert await load_requisition(requisition_id) is None
        assert await load_approval(requisition_id) is None

    finally:
        await cleanup(requisition_id=requisition_id)

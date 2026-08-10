from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from procurement_service.core.enums import (
    ApprovalObjectType,
    ApprovalRequestStatus,
    ApprovalStepStatus,
)
from procurement_service.db.session import AsyncSessionFactory, engine
from procurement_service.models import (
    ProcurementApprovalRequest,
)
from procurement_service.repositories import (
    ProcurementApprovalRepository,
)
from procurement_service.schemas.approval import (
    ProcurementApprovalRequestCreate,
    ProcurementApprovalStepCreate,
)
from procurement_service.services import (
    ApprovalWorkflowService,
)



@pytest_asyncio.fixture(
    scope="module",
    loop_scope="module",
    autouse=True,
)
async def isolate_async_engine_pool():
    # Each PostgreSQL integration module owns a distinct
    # pytest asyncio event loop. Never allow pooled asyncpg
    # connections created by one module loop to be reused
    # by another module loop.
    await engine.dispose(close=False)

    try:
        yield
    finally:
        # Teardown occurs while this module's event loop is
        # still alive, so its pooled connections can be
        # closed cleanly.
        await engine.dispose()

def build_payload(
    *,
    object_id=None,
    step_count: int = 2,
):
    return ProcurementApprovalRequestCreate(
        object_type=ApprovalObjectType.PURCHASE_ORDER,
        object_id=object_id or uuid4(),
        requested_by=uuid4(),
        comments="integration test approval",
        steps=[
            ProcurementApprovalStepCreate(
                step_number=number,
                approver_id=uuid4(),
            )
            for number in range(
                1,
                step_count + 1,
            )
        ],
    )


@pytest.mark.asyncio(loop_scope="module")
async def test_real_postgres_add_and_get_by_id():
    tenant_id = uuid4()

    async with AsyncSessionFactory() as session:
        repository = ProcurementApprovalRepository(
            session
        )

        request = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=build_payload(
                step_count=2,
            ),
        )

        try:
            await repository.add(request)

            loaded = await repository.get_by_id(
                tenant_id=tenant_id,
                request_id=request.id,
            )

            assert loaded is not None
            assert loaded.id == request.id
            assert loaded.tenant_id == tenant_id

            assert (
                loaded.status
                == ApprovalRequestStatus.PENDING
            )

            assert len(loaded.steps) == 2

            assert sorted(
                step.step_number
                for step in loaded.steps
            ) == [1, 2]

            assert all(
                step.tenant_id == tenant_id
                for step in loaded.steps
            )

            assert all(
                step.status
                == ApprovalStepStatus.PENDING
                for step in loaded.steps
            )

        finally:
            await session.rollback()


@pytest.mark.asyncio(loop_scope="module")
async def test_real_postgres_get_by_object():
    tenant_id = uuid4()
    object_id = uuid4()

    async with AsyncSessionFactory() as session:
        repository = ProcurementApprovalRepository(
            session
        )

        request = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=build_payload(
                object_id=object_id,
                step_count=1,
            ),
        )

        try:
            await repository.add(request)

            loaded = await repository.get_by_object(
                tenant_id=tenant_id,
                object_type=(
                    ApprovalObjectType.PURCHASE_ORDER
                ),
                object_id=object_id,
            )

            assert loaded is not None
            assert loaded.id == request.id
            assert loaded.object_id == object_id
            assert loaded.tenant_id == tenant_id
            assert len(loaded.steps) == 1

        finally:
            await session.rollback()


@pytest.mark.asyncio(loop_scope="module")
async def test_real_postgres_tenant_isolation_by_id():
    owning_tenant = uuid4()
    foreign_tenant = uuid4()

    async with AsyncSessionFactory() as session:
        repository = ProcurementApprovalRepository(
            session
        )

        request = ApprovalWorkflowService.create_request(
            tenant_id=owning_tenant,
            payload=build_payload(
                step_count=1,
            ),
        )

        try:
            await repository.add(request)

            foreign_result = await repository.get_by_id(
                tenant_id=foreign_tenant,
                request_id=request.id,
            )

            owning_result = await repository.get_by_id(
                tenant_id=owning_tenant,
                request_id=request.id,
            )

            assert foreign_result is None
            assert owning_result is not None
            assert owning_result.id == request.id

        finally:
            await session.rollback()


@pytest.mark.asyncio(loop_scope="module")
async def test_real_postgres_tenant_isolation_by_object():
    owning_tenant = uuid4()
    foreign_tenant = uuid4()
    object_id = uuid4()

    async with AsyncSessionFactory() as session:
        repository = ProcurementApprovalRepository(
            session
        )

        request = ApprovalWorkflowService.create_request(
            tenant_id=owning_tenant,
            payload=build_payload(
                object_id=object_id,
                step_count=1,
            ),
        )

        try:
            await repository.add(request)

            foreign_result = (
                await repository.get_by_object(
                    tenant_id=foreign_tenant,
                    object_type=(
                        ApprovalObjectType.PURCHASE_ORDER
                    ),
                    object_id=object_id,
                )
            )

            owning_result = (
                await repository.get_by_object(
                    tenant_id=owning_tenant,
                    object_type=(
                        ApprovalObjectType.PURCHASE_ORDER
                    ),
                    object_id=object_id,
                )
            )

            assert foreign_result is None
            assert owning_result is not None

        finally:
            await session.rollback()


@pytest.mark.asyncio(loop_scope="module")
async def test_real_postgres_for_update_loads_request():
    tenant_id = uuid4()

    async with AsyncSessionFactory() as session:
        repository = ProcurementApprovalRepository(
            session
        )

        request = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=build_payload(
                step_count=2,
            ),
        )

        try:
            await repository.add(request)

            locked = await repository.get_by_id(
                tenant_id=tenant_id,
                request_id=request.id,
                for_update=True,
            )

            assert locked is not None
            assert locked.id == request.id
            assert len(locked.steps) == 2

        finally:
            await session.rollback()


@pytest.mark.asyncio(loop_scope="module")
async def test_real_postgres_rollback_removes_request():
    tenant_id = uuid4()

    request_id = None

    async with AsyncSessionFactory() as session:
        repository = ProcurementApprovalRepository(
            session
        )

        request = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=build_payload(
                step_count=1,
            ),
        )

        request_id = request.id

        await repository.add(request)

        statement = select(
            func.count()
        ).select_from(
            ProcurementApprovalRequest
        ).where(
            ProcurementApprovalRequest.id
            == request_id
        )

        count_before = await session.scalar(
            statement
        )

        assert count_before == 1

        await session.rollback()

    async with AsyncSessionFactory() as verify_session:
        count_after = await verify_session.scalar(
            select(func.count())
            .select_from(
                ProcurementApprovalRequest
            )
            .where(
                ProcurementApprovalRequest.id
                == request_id
            )
        )

        assert count_after == 0


@pytest.mark.asyncio(loop_scope="module")
async def test_real_postgres_duplicate_object_guard():
    tenant_id = uuid4()
    object_id = uuid4()

    async with AsyncSessionFactory() as session:
        repository = ProcurementApprovalRepository(
            session
        )

        first = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=build_payload(
                object_id=object_id,
                step_count=1,
            ),
        )

        second = ApprovalWorkflowService.create_request(
            tenant_id=tenant_id,
            payload=build_payload(
                object_id=object_id,
                step_count=1,
            ),
        )

        try:
            await repository.add(first)

            with pytest.raises(IntegrityError):
                await repository.add(second)

        finally:
            await session.rollback()

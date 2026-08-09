from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.sql import Select

from procurement_service.core.enums import (
    ApprovalObjectType,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
)
from procurement_service.repositories import (
    ProcurementApprovalRepository,
)


@pytest.mark.asyncio
async def test_add_registers_and_flushes_request():
    session = MagicMock()
    session.flush = AsyncMock()

    repository = ProcurementApprovalRepository(session)

    approval_request = MagicMock(
        spec=ProcurementApprovalRequest
    )

    result = await repository.add(approval_request)

    session.add.assert_called_once_with(approval_request)
    session.flush.assert_awaited_once_with()

    assert result is approval_request


@pytest.mark.asyncio
async def test_get_by_id_executes_tenant_scoped_query():
    request = MagicMock(
        spec=ProcurementApprovalRequest
    )

    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = request

    session = MagicMock()
    session.execute = AsyncMock(
        return_value=scalar_result
    )

    repository = ProcurementApprovalRepository(session)

    result = await repository.get_by_id(
        tenant_id=uuid4(),
        request_id=uuid4(),
    )

    assert result is request

    session.execute.assert_awaited_once()

    statement = session.execute.await_args.args[0]

    assert isinstance(statement, Select)


@pytest.mark.asyncio
async def test_get_by_id_can_request_row_lock():
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = None

    session = MagicMock()
    session.execute = AsyncMock(
        return_value=scalar_result
    )

    repository = ProcurementApprovalRepository(session)

    await repository.get_by_id(
        tenant_id=uuid4(),
        request_id=uuid4(),
        for_update=True,
    )

    statement = session.execute.await_args.args[0]

    sql = str(statement)

    assert "FOR UPDATE" in sql


@pytest.mark.asyncio
async def test_get_by_object_executes_query():
    request = MagicMock(
        spec=ProcurementApprovalRequest
    )

    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = request

    session = MagicMock()
    session.execute = AsyncMock(
        return_value=scalar_result
    )

    repository = ProcurementApprovalRepository(session)

    result = await repository.get_by_object(
        tenant_id=uuid4(),
        object_type=(
            ApprovalObjectType.PURCHASE_ORDER
        ),
        object_id=uuid4(),
    )

    assert result is request
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_object_can_request_row_lock():
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = None

    session = MagicMock()
    session.execute = AsyncMock(
        return_value=scalar_result
    )

    repository = ProcurementApprovalRepository(session)

    await repository.get_by_object(
        tenant_id=uuid4(),
        object_type=(
            ApprovalObjectType.PURCHASE_ORDER
        ),
        object_id=uuid4(),
        for_update=True,
    )

    statement = session.execute.await_args.args[0]

    assert "FOR UPDATE" in str(statement)


@pytest.mark.asyncio
async def test_flush_delegates_to_session():
    session = MagicMock()
    session.flush = AsyncMock()

    repository = ProcurementApprovalRepository(session)

    await repository.flush()

    session.flush.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_refresh_delegates_to_session():
    session = MagicMock()
    session.refresh = AsyncMock()

    repository = ProcurementApprovalRepository(session)

    approval_request = MagicMock(
        spec=ProcurementApprovalRequest
    )

    await repository.refresh(approval_request)

    session.refresh.assert_awaited_once_with(
        approval_request
    )

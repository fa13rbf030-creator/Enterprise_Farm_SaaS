from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select

from procurement_service.core.config import get_settings
from procurement_service.db.session import AsyncSessionFactory, engine
from procurement_service.main import app
from procurement_service.models import (
    ProcurementApprovalRequest,
    ProcurementApprovalStep,
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

def make_access_token(
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "access",
        "iss": settings.token_issuer,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
        "jti": str(uuid4()),
        "permissions": permissions,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def auth_headers(
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
    header_tenant_id: UUID | None = None,
) -> dict[str, str]:
    token = make_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        permissions=permissions,
    )

    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(
            header_tenant_id or tenant_id
        ),
    }


def create_payload(
    *,
    user_id: UUID,
    object_id: UUID,
) -> dict:
    return {
        "object_type": "PURCHASE_ORDER",
        "object_id": str(object_id),
        "requested_by": str(user_id),
        "comments": "HTTP postgres integration test",
        "steps": [
            {
                "step_number": 1,
                "approver_id": str(uuid4()),
            },
            {
                "step_number": 2,
                "approver_id": str(uuid4()),
            },
        ],
    }


async def cleanup_request(
    request_id: UUID,
) -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(
            delete(ProcurementApprovalStep).where(
                ProcurementApprovalStep.approval_request_id
                == request_id
            )
        )

        await session.execute(
            delete(ProcurementApprovalRequest).where(
                ProcurementApprovalRequest.id
                == request_id
            )
        )

        await session.commit()


async def request_count(
    request_id: UUID,
) -> int:
    async with AsyncSessionFactory() as session:
        result = await session.scalar(
            select(func.count())
            .select_from(
                ProcurementApprovalRequest
            )
            .where(
                ProcurementApprovalRequest.id
                == request_id
            )
        )

        return int(result or 0)


@pytest.mark.asyncio(loop_scope="module")
async def test_http_create_commits_and_read_is_tenant_scoped():
    owner_user_id = uuid4()
    owner_tenant_id = uuid4()
    foreign_tenant_id = uuid4()
    object_id = uuid4()

    request_id = None

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            create_response = await client.post(
                "/approvals",
                headers=auth_headers(
                    user_id=owner_user_id,
                    tenant_id=owner_tenant_id,
                    permissions=[
                        "procurement.approvals.create",
                    ],
                ),
                json=create_payload(
                    user_id=owner_user_id,
                    object_id=object_id,
                ),
            )

            assert create_response.status_code == 201, (
                create_response.text
            )

            created = create_response.json()

            request_id = UUID(created["id"])

            assert (
                UUID(created["tenant_id"])
                == owner_tenant_id
            )

            assert (
                UUID(created["object_id"])
                == object_id
            )

            assert (
                UUID(created["requested_by"])
                == owner_user_id
            )

            assert created["status"] == "PENDING"
            assert created["current_step"] == 1
            assert created["total_steps"] == 2
            assert len(created["steps"]) == 2

            # A new DB session proves the endpoint committed.
            assert await request_count(request_id) == 1

            owner_read = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=owner_user_id,
                    tenant_id=owner_tenant_id,
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert owner_read.status_code == 200, (
                owner_read.text
            )

            loaded = owner_read.json()

            assert UUID(loaded["id"]) == request_id

            assert (
                UUID(loaded["tenant_id"])
                == owner_tenant_id
            )

            assert (
                UUID(loaded["object_id"])
                == object_id
            )

            assert loaded["status"] == "PENDING"
            assert len(loaded["steps"]) == 2

            foreign_read = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=uuid4(),
                    tenant_id=foreign_tenant_id,
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert foreign_read.status_code == 404

            assert foreign_read.json()["detail"] == (
                "Approval request not found"
            )

    finally:
        if request_id is not None:
            await cleanup_request(request_id)

    assert request_id is not None
    assert await request_count(request_id) == 0


@pytest.mark.asyncio(loop_scope="module")
async def test_http_two_step_approval_commits_terminal_state():
    requester_id = uuid4()
    approver_one_id = uuid4()
    approver_two_id = uuid4()
    tenant_id = uuid4()
    object_id = uuid4()

    request_id = None

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            payload = create_payload(
                user_id=requester_id,
                object_id=object_id,
            )

            payload["steps"][0]["approver_id"] = str(
                approver_one_id
            )
            payload["steps"][1]["approver_id"] = str(
                approver_two_id
            )

            create_response = await client.post(
                "/approvals",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create",
                    ],
                ),
                json=payload,
            )

            assert create_response.status_code == 201, (
                create_response.text
            )

            created = create_response.json()
            request_id = UUID(created["id"])

            assert created["status"] == "PENDING"
            assert created["current_step"] == 1

            first_response = await client.post(
                (
                    f"/approvals/{request_id}"
                    "/steps/1/approve"
                ),
                headers=auth_headers(
                    user_id=approver_one_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.approve",
                    ],
                ),
                json={
                    "decided_by": str(approver_one_id),
                    "comments": "HTTP step one approved",
                },
            )

            assert first_response.status_code == 200, (
                first_response.text
            )

            after_first = first_response.json()

            assert after_first["status"] == "IN_PROGRESS"
            assert after_first["current_step"] == 2

            steps = {
                step["step_number"]: step
                for step in after_first["steps"]
            }

            assert steps[1]["status"] == "APPROVED"
            assert (
                UUID(steps[1]["decided_by"])
                == approver_one_id
            )
            assert (
                steps[1]["comments"]
                == "HTTP step one approved"
            )
            assert steps[2]["status"] == "PENDING"

            # Read through a separate HTTP request after the
            # first decision. This verifies the first endpoint
            # committed before the second decision.
            persisted_first = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert persisted_first.status_code == 200, (
                persisted_first.text
            )

            persisted_first_body = persisted_first.json()

            assert (
                persisted_first_body["status"]
                == "IN_PROGRESS"
            )
            assert (
                persisted_first_body["current_step"]
                == 2
            )

            second_response = await client.post(
                (
                    f"/approvals/{request_id}"
                    "/steps/2/approve"
                ),
                headers=auth_headers(
                    user_id=approver_two_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.approve",
                    ],
                ),
                json={
                    "decided_by": str(approver_two_id),
                    "comments": "HTTP step two approved",
                },
            )

            assert second_response.status_code == 200, (
                second_response.text
            )

            approved = second_response.json()

            assert approved["status"] == "APPROVED"
            assert approved["current_step"] == 2
            assert approved["completed_at"] is not None

            approved_steps = {
                step["step_number"]: step
                for step in approved["steps"]
            }

            assert (
                approved_steps[1]["status"]
                == "APPROVED"
            )
            assert (
                approved_steps[2]["status"]
                == "APPROVED"
            )

            assert (
                UUID(approved_steps[2]["decided_by"])
                == approver_two_id
            )

            assert (
                approved_steps[2]["comments"]
                == "HTTP step two approved"
            )

            # Final GET verifies terminal state survived
            # endpoint commit and reload.
            final_read = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert final_read.status_code == 200, (
                final_read.text
            )

            persisted = final_read.json()

            assert persisted["status"] == "APPROVED"
            assert persisted["completed_at"] is not None
            assert persisted["current_step"] == 2

            persisted_steps = {
                step["step_number"]: step
                for step in persisted["steps"]
            }

            assert (
                persisted_steps[1]["status"]
                == "APPROVED"
            )
            assert (
                persisted_steps[2]["status"]
                == "APPROVED"
            )

            # Tenant isolation must remain true even after
            # the request reaches terminal APPROVED state.
            foreign_read = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=uuid4(),
                    tenant_id=uuid4(),
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert foreign_read.status_code == 404
            assert foreign_read.json()["detail"] == (
                "Approval request not found"
            )

        assert await request_count(request_id) == 1

    finally:
        if request_id is not None:
            await cleanup_request(request_id)

    assert request_id is not None
    assert await request_count(request_id) == 0


@pytest.mark.asyncio(loop_scope="module")
async def test_http_rejection_commits_terminal_state():
    requester_id = uuid4()
    approver_one_id = uuid4()
    approver_two_id = uuid4()
    tenant_id = uuid4()
    object_id = uuid4()

    request_id = None

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            payload = create_payload(
                user_id=requester_id,
                object_id=object_id,
            )

            payload["steps"][0]["approver_id"] = str(
                approver_one_id
            )
            payload["steps"][1]["approver_id"] = str(
                approver_two_id
            )

            create_response = await client.post(
                "/approvals",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create",
                    ],
                ),
                json=payload,
            )

            assert create_response.status_code == 201, (
                create_response.text
            )

            created = create_response.json()
            request_id = UUID(created["id"])

            assert created["status"] == "PENDING"
            assert created["current_step"] == 1

            reject_response = await client.post(
                (
                    f"/approvals/{request_id}"
                    "/steps/1/reject"
                ),
                headers=auth_headers(
                    user_id=approver_one_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.reject",
                    ],
                ),
                json={
                    "decided_by": str(approver_one_id),
                    "comments": "HTTP rejection test",
                },
            )

            assert reject_response.status_code == 200, (
                reject_response.text
            )

            rejected = reject_response.json()

            assert rejected["status"] == "REJECTED"
            assert rejected["completed_at"] is not None

            steps = {
                step["step_number"]: step
                for step in rejected["steps"]
            }

            assert steps[1]["status"] == "REJECTED"
            assert (
                UUID(steps[1]["decided_by"])
                == approver_one_id
            )
            assert (
                steps[1]["comments"]
                == "HTTP rejection test"
            )

            assert steps[2]["status"] == "SKIPPED"
            assert steps[2]["decided_by"] is None

            persisted_response = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert persisted_response.status_code == 200, (
                persisted_response.text
            )

            persisted = persisted_response.json()

            assert persisted["status"] == "REJECTED"
            assert persisted["completed_at"] is not None

            persisted_steps = {
                step["step_number"]: step
                for step in persisted["steps"]
            }

            assert (
                persisted_steps[1]["status"]
                == "REJECTED"
            )
            assert (
                persisted_steps[2]["status"]
                == "SKIPPED"
            )

            # A terminal REJECTED request must reject any
            # subsequent decision attempt.
            terminal_response = await client.post(
                (
                    f"/approvals/{request_id}"
                    "/steps/1/approve"
                ),
                headers=auth_headers(
                    user_id=approver_one_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.approve",
                    ],
                ),
                json={
                    "decided_by": str(approver_one_id),
                    "comments": (
                        "should not mutate terminal request"
                    ),
                },
            )

            assert terminal_response.status_code == 409

            # Verify failed terminal mutation did not alter
            # the already-committed rejection state.
            after_conflict = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert after_conflict.status_code == 200

            after_conflict_body = after_conflict.json()

            assert (
                after_conflict_body["status"]
                == "REJECTED"
            )

            after_conflict_steps = {
                step["step_number"]: step
                for step in after_conflict_body["steps"]
            }

            assert (
                after_conflict_steps[1]["status"]
                == "REJECTED"
            )
            assert (
                after_conflict_steps[2]["status"]
                == "SKIPPED"
            )

        assert await request_count(request_id) == 1

    finally:
        if request_id is not None:
            await cleanup_request(request_id)

    assert request_id is not None
    assert await request_count(request_id) == 0


@pytest.mark.asyncio(loop_scope="module")
async def test_http_cancel_commits_terminal_state():
    requester_id = uuid4()
    tenant_id = uuid4()
    object_id = uuid4()

    request_id = None

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            payload = create_payload(
                user_id=requester_id,
                object_id=object_id,
            )

            create_response = await client.post(
                "/approvals",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.create",
                    ],
                ),
                json=payload,
            )

            assert create_response.status_code == 201, (
                create_response.text
            )

            created = create_response.json()
            request_id = UUID(created["id"])

            assert created["status"] == "PENDING"
            assert created["completed_at"] is None

            cancel_response = await client.post(
                f"/approvals/{request_id}/cancel",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.cancel",
                    ],
                ),
                json={
                    "comments": "HTTP cancellation test",
                },
            )

            assert cancel_response.status_code == 200, (
                cancel_response.text
            )

            cancelled = cancel_response.json()

            assert cancelled["status"] == "CANCELLED"
            assert cancelled["completed_at"] is not None

            persisted_response = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert persisted_response.status_code == 200, (
                persisted_response.text
            )

            persisted = persisted_response.json()

            assert persisted["status"] == "CANCELLED"
            assert persisted["completed_at"] is not None

            terminal_approve = await client.post(
                (
                    f"/approvals/{request_id}"
                    "/steps/1/approve"
                ),
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.approve",
                    ],
                ),
                json={
                    "decided_by": str(requester_id),
                    "comments": "should fail",
                },
            )

            assert terminal_approve.status_code == 409

            terminal_reject = await client.post(
                (
                    f"/approvals/{request_id}"
                    "/steps/1/reject"
                ),
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.reject",
                    ],
                ),
                json={
                    "decided_by": str(requester_id),
                    "comments": "should fail",
                },
            )

            assert terminal_reject.status_code == 409

            terminal_cancel = await client.post(
                f"/approvals/{request_id}/cancel",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.cancel",
                    ],
                ),
                json={
                    "comments": "second cancel should fail",
                },
            )

            assert terminal_cancel.status_code == 409

            after_conflict = await client.get(
                f"/approvals/{request_id}",
                headers=auth_headers(
                    user_id=requester_id,
                    tenant_id=tenant_id,
                    permissions=[
                        "procurement.approvals.read",
                    ],
                ),
            )

            assert after_conflict.status_code == 200

            after_conflict_body = (
                after_conflict.json()
            )

            assert (
                after_conflict_body["status"]
                == "CANCELLED"
            )
            assert (
                after_conflict_body["completed_at"]
                is not None
            )

        assert await request_count(request_id) == 1

    finally:
        if request_id is not None:
            await cleanup_request(request_id)

    assert request_id is not None
    assert await request_count(request_id) == 0

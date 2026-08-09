from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from procurement_service.core.enums import (
    ApprovalObjectType,
)
from procurement_service.models import (
    ProcurementApprovalRequest,
)


class ProcurementApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        approval_request: ProcurementApprovalRequest,
    ) -> ProcurementApprovalRequest:
        self.session.add(approval_request)
        await self.session.flush()

        return approval_request

    async def get_by_id(
        self,
        *,
        tenant_id: UUID,
        request_id: UUID,
        for_update: bool = False,
    ) -> ProcurementApprovalRequest | None:
        statement = (
            select(ProcurementApprovalRequest)
            .where(
                ProcurementApprovalRequest.id == request_id,
                ProcurementApprovalRequest.tenant_id == tenant_id,
            )
            .options(
                selectinload(
                    ProcurementApprovalRequest.steps
                )
            )
        )

        if for_update:
            statement = statement.with_for_update()

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_object(
        self,
        *,
        tenant_id: UUID,
        object_type: ApprovalObjectType,
        object_id: UUID,
        for_update: bool = False,
    ) -> ProcurementApprovalRequest | None:
        statement = (
            select(ProcurementApprovalRequest)
            .where(
                ProcurementApprovalRequest.tenant_id == tenant_id,
                ProcurementApprovalRequest.object_type == object_type,
                ProcurementApprovalRequest.object_id == object_id,
            )
            .options(
                selectinload(
                    ProcurementApprovalRequest.steps
                )
            )
        )

        if for_update:
            statement = statement.with_for_update()

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def flush(self) -> None:
        await self.session.flush()

    async def refresh(
        self,
        approval_request: ProcurementApprovalRequest,
    ) -> None:
        await self.session.refresh(approval_request)

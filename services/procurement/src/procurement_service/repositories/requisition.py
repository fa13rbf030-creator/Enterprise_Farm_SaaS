from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from procurement_service.models import (
    PurchaseRequisition,
)


class PurchaseRequisitionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        *,
        tenant_id: UUID,
        requisition_id: UUID,
        for_update: bool = False,
    ) -> PurchaseRequisition | None:
        statement = (
            select(PurchaseRequisition)
            .where(
                PurchaseRequisition.id == requisition_id,
                PurchaseRequisition.tenant_id == tenant_id,
            )
            .options(
                selectinload(PurchaseRequisition.lines)
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
        requisition: PurchaseRequisition,
    ) -> None:
        await self.session.refresh(requisition)

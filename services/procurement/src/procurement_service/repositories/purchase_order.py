from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from procurement_service.models import PurchaseOrder


class PurchaseOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self,
        *,
        tenant_id: UUID,
        purchase_order_id: UUID,
        for_update: bool = False,
    ) -> PurchaseOrder | None:
        statement = select(PurchaseOrder).where(
            PurchaseOrder.id == purchase_order_id,
            PurchaseOrder.tenant_id == tenant_id,
        )

        if for_update:
            statement = statement.with_for_update()

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from procurement_service.models import SupplierInvoiceMatch


class SupplierInvoiceMatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        *,
        tenant_id: UUID,
        invoice_match_id: UUID,
        for_update: bool = False,
    ) -> SupplierInvoiceMatch | None:
        statement = select(SupplierInvoiceMatch).where(
            SupplierInvoiceMatch.id == invoice_match_id,
            SupplierInvoiceMatch.tenant_id == tenant_id,
        )

        if for_update:
            statement = statement.with_for_update()

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def flush(self) -> None:
        await self.session.flush()

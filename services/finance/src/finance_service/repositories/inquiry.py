from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    JournalSource,
    JournalStatus,
)
from finance_service.models.gl import (
    JournalEntry,
    JournalLine,
    LedgerAccount,
)
from finance_service.models.posting import AccountBalance


async def list_account_activity(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    ledger_account_id: UUID,
    fiscal_period_id: UUID,
) -> list[tuple[JournalEntry, JournalLine]]:
    result = await session.execute(
        select(JournalEntry, JournalLine)
        .join(
            JournalLine,
            JournalLine.journal_entry_id == JournalEntry.id,
        )
        .where(
            JournalEntry.tenant_id == tenant_id,
            JournalEntry.fiscal_period_id == fiscal_period_id,
            JournalLine.tenant_id == tenant_id,
            JournalLine.ledger_account_id == ledger_account_id,
            JournalEntry.status.in_(
                [
                    JournalStatus.POSTED,
                    JournalStatus.REVERSED,
                ]
            ),
        )
        .order_by(
            JournalEntry.entry_date,
            JournalEntry.created_at,
            JournalLine.line_number,
        )
    )

    return list(result.all())


async def get_account_balance_for_period(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    ledger_account_id: UUID,
    fiscal_period_id: UUID,
) -> AccountBalance | None:
    result = await session.execute(
        select(AccountBalance).where(
            AccountBalance.tenant_id == tenant_id,
            AccountBalance.ledger_account_id
            == ledger_account_id,
            AccountBalance.fiscal_period_id
            == fiscal_period_id,
        )
    )

    return result.scalar_one_or_none()


async def search_journals(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_period_id: UUID | None = None,
    status: JournalStatus | None = None,
    source: JournalSource | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    journal_number: str | None = None,
    limit: int = 100,
) -> list[JournalEntry]:
    query = select(JournalEntry).where(
        JournalEntry.tenant_id == tenant_id
    )

    if fiscal_period_id is not None:
        query = query.where(
            JournalEntry.fiscal_period_id
            == fiscal_period_id
        )

    if status is not None:
        query = query.where(
            JournalEntry.status == status
        )

    if source is not None:
        query = query.where(
            JournalEntry.source == source
        )

    if date_from is not None:
        query = query.where(
            JournalEntry.entry_date >= date_from
        )

    if date_to is not None:
        query = query.where(
            JournalEntry.entry_date <= date_to
        )

    if journal_number:
        query = query.where(
            JournalEntry.journal_number.ilike(
                f"%{journal_number.strip()}%"
            )
        )

    result = await session.execute(
        query.order_by(
            JournalEntry.entry_date.desc(),
            JournalEntry.created_at.desc(),
        ).limit(limit)
    )

    return list(result.scalars().all())


async def get_ledger_account_for_inquiry(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    ledger_account_id: UUID,
) -> LedgerAccount | None:
    result = await session.execute(
        select(LedgerAccount).where(
            LedgerAccount.tenant_id == tenant_id,
            LedgerAccount.id == ledger_account_id,
        )
    )

    return result.scalar_one_or_none()

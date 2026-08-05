from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.gl import (
    FiscalPeriod,
    JournalEntry,
    JournalLine,
    LedgerAccount,
)
from finance_service.models.posting import (
    AccountBalance,
    PostingAudit,
)


async def get_balance(
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


async def list_period_balances(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_period_id: UUID,
) -> list[tuple[AccountBalance, LedgerAccount]]:
    result = await session.execute(
        select(AccountBalance, LedgerAccount)
        .join(
            LedgerAccount,
            LedgerAccount.id
            == AccountBalance.ledger_account_id,
        )
        .where(
            AccountBalance.tenant_id == tenant_id,
            AccountBalance.fiscal_period_id
            == fiscal_period_id,
        )
        .order_by(LedgerAccount.code)
    )

    return list(result.all())


async def list_journal_lines_for_posting(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    journal_entry_id: UUID,
) -> list[tuple[JournalLine, LedgerAccount]]:
    result = await session.execute(
        select(JournalLine, LedgerAccount)
        .join(
            LedgerAccount,
            LedgerAccount.id
            == JournalLine.ledger_account_id,
        )
        .where(
            JournalLine.tenant_id == tenant_id,
            JournalLine.journal_entry_id
            == journal_entry_id,
        )
        .order_by(JournalLine.line_number)
    )

    return list(result.all())


async def create_posting_audit(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    journal_entry_id: UUID,
    action: str,
    actor_id: UUID,
    previous_status: str,
    new_status: str,
    details: str = "",
) -> PostingAudit:
    record = PostingAudit(
        tenant_id=tenant_id,
        journal_entry_id=journal_entry_id,
        action=action,
        actor_id=actor_id,
        previous_status=previous_status,
        new_status=new_status,
        details=details,
    )

    session.add(record)
    await session.flush()

    return record


async def get_period_with_lock(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_period_id: UUID,
) -> FiscalPeriod | None:
    result = await session.execute(
        select(FiscalPeriod)
        .where(
            FiscalPeriod.id == fiscal_period_id,
            FiscalPeriod.tenant_id == tenant_id,
        )
        .with_for_update()
    )

    return result.scalar_one_or_none()


async def get_journal_with_lock(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    journal_id: UUID,
) -> JournalEntry | None:
    result = await session.execute(
        select(JournalEntry)
        .where(
            JournalEntry.id == journal_id,
            JournalEntry.tenant_id == tenant_id,
        )
        .with_for_update()
    )

    return result.scalar_one_or_none()

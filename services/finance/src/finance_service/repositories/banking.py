from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.models.banking import (
    BankAccount,
    BankReconciliation,
    BankReconciliationMatch,
    BankStatement,
    BankStatementLine,
)
from finance_service.models.gl import JournalEntry


async def get_bank_account(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    bank_account_id: UUID,
    for_update: bool = False,
) -> BankAccount | None:
    query = select(BankAccount).where(
        BankAccount.id == bank_account_id,
        BankAccount.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_bank_accounts(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    currency_code: str | None = None,
) -> list[BankAccount]:
    query = select(BankAccount).where(
        BankAccount.tenant_id == tenant_id
    )

    if currency_code:
        query = query.where(
            BankAccount.currency_code
            == currency_code.upper()
        )

    result = await session.execute(
        query.order_by(BankAccount.account_code)
    )

    return list(result.scalars().all())


async def get_bank_statement(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    statement_id: UUID,
    for_update: bool = False,
) -> BankStatement | None:
    query = select(BankStatement).where(
        BankStatement.id == statement_id,
        BankStatement.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_statement_lines(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    statement_id: UUID,
    unreconciled_only: bool = False,
) -> list[BankStatementLine]:
    query = select(BankStatementLine).where(
        BankStatementLine.tenant_id == tenant_id,
        BankStatementLine.statement_id == statement_id,
    )

    if unreconciled_only:
        query = query.where(
            BankStatementLine.is_reconciled.is_(False)
        )

    result = await session.execute(
        query.order_by(BankStatementLine.line_number)
    )

    return list(result.scalars().all())


async def get_statement_line(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    statement_line_id: UUID,
    for_update: bool = False,
) -> BankStatementLine | None:
    query = select(BankStatementLine).where(
        BankStatementLine.id == statement_line_id,
        BankStatementLine.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_reconciliation(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    reconciliation_id: UUID,
    for_update: bool = False,
) -> BankReconciliation | None:
    query = select(BankReconciliation).where(
        BankReconciliation.id == reconciliation_id,
        BankReconciliation.tenant_id == tenant_id,
    )

    if for_update:
        query = query.with_for_update()

    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_reconciliation_matches(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    reconciliation_id: UUID,
) -> list[BankReconciliationMatch]:
    result = await session.execute(
        select(BankReconciliationMatch)
        .where(
            BankReconciliationMatch.tenant_id
            == tenant_id,
            BankReconciliationMatch.reconciliation_id
            == reconciliation_id,
        )
        .order_by(
            BankReconciliationMatch.matched_at
        )
    )

    return list(result.scalars().all())


async def get_reconciliation_match_for_line(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    reconciliation_id: UUID,
    statement_line_id: UUID,
) -> BankReconciliationMatch | None:
    result = await session.execute(
        select(BankReconciliationMatch).where(
            BankReconciliationMatch.tenant_id
            == tenant_id,
            BankReconciliationMatch.reconciliation_id
            == reconciliation_id,
            BankReconciliationMatch.statement_line_id
            == statement_line_id,
        )
    )

    return result.scalar_one_or_none()


async def get_posted_journal(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    journal_entry_id: UUID,
) -> JournalEntry | None:
    result = await session.execute(
        select(JournalEntry).where(
            JournalEntry.id == journal_entry_id,
            JournalEntry.tenant_id == tenant_id,
        )
    )

    return result.scalar_one_or_none()

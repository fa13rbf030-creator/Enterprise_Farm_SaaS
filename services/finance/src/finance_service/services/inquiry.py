from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    JournalSource,
    JournalStatus,
)
from finance_service.repositories.inquiry import (
    get_account_balance_for_period,
    get_ledger_account_for_inquiry,
    list_account_activity,
    search_journals,
)
from finance_service.schemas.inquiry import (
    JournalSearchItem,
    LedgerInquiryLine,
    LedgerInquiryRead,
)
from finance_service.services.balances import (
    calculate_net_balance,
)


class InquiryValidationError(ValueError):
    pass


async def build_ledger_inquiry(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    ledger_account_id: UUID,
    fiscal_period_id: UUID,
) -> LedgerInquiryRead:
    account = await get_ledger_account_for_inquiry(
        session,
        tenant_id=tenant_id,
        ledger_account_id=ledger_account_id,
    )

    if account is None:
        raise InquiryValidationError(
            "Ledger account not found"
        )

    balance = await get_account_balance_for_period(
        session,
        tenant_id=tenant_id,
        ledger_account_id=ledger_account_id,
        fiscal_period_id=fiscal_period_id,
    )

    opening_debit = (
        balance.opening_debit
        if balance is not None
        else Decimal("0")
    )
    opening_credit = (
        balance.opening_credit
        if balance is not None
        else Decimal("0")
    )

    activity = await list_account_activity(
        session,
        tenant_id=tenant_id,
        ledger_account_id=ledger_account_id,
        fiscal_period_id=fiscal_period_id,
    )

    cumulative_debit = opening_debit
    cumulative_credit = opening_credit
    lines: list[LedgerInquiryLine] = []

    for journal, line in activity:
        cumulative_debit += line.base_debit
        cumulative_credit += line.base_credit

        running_debit, running_credit = (
            calculate_net_balance(
                debit=cumulative_debit,
                credit=cumulative_credit,
                normal_balance=account.normal_balance,
            )
        )

        lines.append(
            LedgerInquiryLine(
                journal_id=journal.id,
                journal_number=journal.journal_number,
                entry_date=journal.entry_date,
                description=journal.description,
                line_description=line.description,
                debit=line.base_debit,
                credit=line.base_credit,
                running_debit=running_debit,
                running_credit=running_credit,
                status=journal.status,
            )
        )

    period_debit = (
        balance.period_debit
        if balance is not None
        else Decimal("0")
    )
    period_credit = (
        balance.period_credit
        if balance is not None
        else Decimal("0")
    )
    closing_debit = (
        balance.closing_debit
        if balance is not None
        else Decimal("0")
    )
    closing_credit = (
        balance.closing_credit
        if balance is not None
        else Decimal("0")
    )

    return LedgerInquiryRead(
        tenant_id=tenant_id,
        ledger_account_id=ledger_account_id,
        account_code=account.code,
        account_name=account.name,
        opening_debit=opening_debit,
        opening_credit=opening_credit,
        period_debit=period_debit,
        period_credit=period_credit,
        closing_debit=closing_debit,
        closing_credit=closing_credit,
        lines=lines,
    )


async def build_journal_search(
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
) -> list[JournalSearchItem]:
    if date_from and date_to and date_to < date_from:
        raise InquiryValidationError(
            "date_to cannot precede date_from"
        )

    journals = await search_journals(
        session,
        tenant_id=tenant_id,
        fiscal_period_id=fiscal_period_id,
        status=status,
        source=source,
        date_from=date_from,
        date_to=date_to,
        journal_number=journal_number,
        limit=limit,
    )

    return [
        JournalSearchItem(
            id=journal.id,
            journal_number=journal.journal_number,
            entry_date=journal.entry_date,
            description=journal.description,
            status=journal.status,
            total_debit=journal.total_debit,
            total_credit=journal.total_credit,
        )
        for journal in journals
    ]

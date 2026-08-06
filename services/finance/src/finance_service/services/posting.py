from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    FiscalPeriodStatus,
    JournalSource,
    JournalStatus,
)
from finance_service.models.gl import (
    JournalEntry,
    JournalLine,
)
from finance_service.models.posting import AccountBalance
from finance_service.repositories.posting import (
    create_posting_audit,
    get_balance,
    get_journal_with_lock,
    get_period_with_lock,
    list_journal_lines_for_posting,
    list_period_balances,
)
from finance_service.schemas.posting import (
    TrialBalanceLine,
    TrialBalanceRead,
)
from finance_service.services.balances import (
    calculate_net_balance,
    determine_balance_direction,
)
from finance_service.services.posting_rules import (
    PostingRuleError,
    validate_journal_can_post,
    validate_journal_can_reverse,
    validate_period_transition,
)


class PostingValidationError(ValueError):
    pass


async def post_journal(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    journal_id: UUID,
    posted_by: UUID,
    allow_closed_period: bool = False,
) -> JournalEntry:
    journal = await get_journal_with_lock(
        session,
        tenant_id=tenant_id,
        journal_id=journal_id,
    )

    if journal is None:
        raise PostingValidationError("Journal not found")

    period = await get_period_with_lock(
        session,
        tenant_id=tenant_id,
        fiscal_period_id=journal.fiscal_period_id,
    )

    if period is None:
        raise PostingValidationError(
            "Fiscal period not found"
        )

    try:
        if allow_closed_period:
            if journal.status != JournalStatus.DRAFT:
                raise PostingRuleError(
                    "Only draft journals can be posted"
                )
        else:
            validate_journal_can_post(
                journal_status=journal.status,
                period_status=period.status,
            )
    except PostingRuleError as exc:
        raise PostingValidationError(str(exc)) from exc

    lines = await list_journal_lines_for_posting(
        session,
        tenant_id=tenant_id,
        journal_entry_id=journal.id,
    )

    if len(lines) < 2:
        raise PostingValidationError(
            "Journal requires at least two lines"
        )

    previous_status = journal.status.value

    for line, account in lines:
        balance = await get_balance(
            session,
            tenant_id=tenant_id,
            ledger_account_id=account.id,
            fiscal_period_id=journal.fiscal_period_id,
        )

        if balance is None:
            balance = AccountBalance(
                tenant_id=tenant_id,
                ledger_account_id=account.id,
                fiscal_period_id=journal.fiscal_period_id,
            )
            session.add(balance)
            await session.flush()

        balance.period_debit += line.base_debit
        balance.period_credit += line.base_credit

        total_debit = (
            balance.opening_debit
            + balance.period_debit
        )
        total_credit = (
            balance.opening_credit
            + balance.period_credit
        )

        (
            balance.closing_debit,
            balance.closing_credit,
        ) = calculate_net_balance(
            debit=total_debit,
            credit=total_credit,
            normal_balance=account.normal_balance,
        )

    journal.status = JournalStatus.POSTED
    journal.posted_by = posted_by
    journal.posted_at = datetime.now(UTC)

    await create_posting_audit(
        session,
        tenant_id=tenant_id,
        journal_entry_id=journal.id,
        action="post",
        actor_id=posted_by,
        previous_status=previous_status,
        new_status=JournalStatus.POSTED.value,
        details="Journal posted and balances updated",
    )

    await session.commit()
    await session.refresh(journal)

    return journal


async def reverse_journal(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    journal_id: UUID,
    reversed_by: UUID,
    reversal_journal_number: str,
    reversal_description: str,
) -> JournalEntry:
    original = await get_journal_with_lock(
        session,
        tenant_id=tenant_id,
        journal_id=journal_id,
    )

    if original is None:
        raise PostingValidationError("Journal not found")

    period = await get_period_with_lock(
        session,
        tenant_id=tenant_id,
        fiscal_period_id=original.fiscal_period_id,
    )

    if period is None:
        raise PostingValidationError(
            "Fiscal period not found"
        )

    try:
        validate_journal_can_reverse(
            journal_status=original.status,
            period_status=period.status,
        )
    except PostingRuleError as exc:
        raise PostingValidationError(str(exc)) from exc

    original_lines = await list_journal_lines_for_posting(
        session,
        tenant_id=tenant_id,
        journal_entry_id=original.id,
    )

    reversal = JournalEntry(
        tenant_id=tenant_id,
        fiscal_period_id=original.fiscal_period_id,
        journal_number=reversal_journal_number.strip(),
        entry_date=original.entry_date,
        source=JournalSource.SYSTEM,
        source_reference=str(original.id),
        description=reversal_description.strip(),
        status=JournalStatus.DRAFT,
        total_debit=original.total_credit,
        total_credit=original.total_debit,
        created_by=reversed_by,
        reversal_of_id=original.id,
    )

    session.add(reversal)
    await session.flush()

    for line, _account in original_lines:
        session.add(
            JournalLine(
                tenant_id=tenant_id,
                journal_entry_id=reversal.id,
                ledger_account_id=line.ledger_account_id,
                line_number=line.line_number,
                description=(
                    f"Reversal: {line.description}"
                ),
                debit=line.credit,
                credit=line.debit,
                currency_code=line.currency_code,
                exchange_rate=line.exchange_rate,
                base_debit=line.base_credit,
                base_credit=line.base_debit,
            )
        )

    await session.flush()

    await post_journal(
        session,
        tenant_id=tenant_id,
        journal_id=reversal.id,
        posted_by=reversed_by,
    )

    original.status = JournalStatus.REVERSED

    await create_posting_audit(
        session,
        tenant_id=tenant_id,
        journal_entry_id=original.id,
        action="reverse",
        actor_id=reversed_by,
        previous_status=JournalStatus.POSTED.value,
        new_status=JournalStatus.REVERSED.value,
        details=f"Reversal journal: {reversal.id}",
    )

    await session.commit()
    await session.refresh(reversal)

    return reversal


async def update_period_status(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_period_id: UUID,
    target_status: FiscalPeriodStatus,
) -> FiscalPeriodStatus:
    period = await get_period_with_lock(
        session,
        tenant_id=tenant_id,
        fiscal_period_id=fiscal_period_id,
    )

    if period is None:
        raise PostingValidationError(
            "Fiscal period not found"
        )

    try:
        validate_period_transition(
            current=period.status,
            target=target_status,
        )
    except PostingRuleError as exc:
        raise PostingValidationError(str(exc)) from exc

    period.status = target_status
    await session.commit()

    return period.status


async def build_trial_balance(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_period_id: UUID,
) -> TrialBalanceRead:
    rows = await list_period_balances(
        session,
        tenant_id=tenant_id,
        fiscal_period_id=fiscal_period_id,
    )

    lines: list[TrialBalanceLine] = []
    total_debit = Decimal("0")
    total_credit = Decimal("0")

    for balance, account in rows:
        debit = balance.closing_debit
        credit = balance.closing_credit

        total_debit += debit
        total_credit += credit

        lines.append(
            TrialBalanceLine(
                ledger_account_id=account.id,
                account_code=account.code,
                account_name=account.name,
                debit=debit,
                credit=credit,
                direction=determine_balance_direction(
                    debit=debit,
                    credit=credit,
                ),
            )
        )

    return TrialBalanceRead(
        tenant_id=tenant_id,
        fiscal_period_id=fiscal_period_id,
        total_debit=total_debit,
        total_credit=total_credit,
        is_balanced=total_debit == total_credit,
        lines=lines,
    )

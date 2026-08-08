from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    AccountType,
    FiscalYearCloseStatus,
    JournalSource,
)
from finance_service.models.closing import FiscalYearCloseRun
from finance_service.repositories.closing import (
    get_year_close_run,
)
from finance_service.repositories.year_close import (
    get_fiscal_year_with_lock,
    get_last_year_period,
    get_retained_earnings_account,
    list_temporary_account_balances,
    list_year_periods,
)
from finance_service.schemas.closing import (
    FiscalYearClosePreview,
    FiscalYearClosePreviewLine,
)
from finance_service.schemas.gl import (
    JournalEntryCreate,
    JournalLineCreate,
)
from finance_service.services.gl import (
    DuplicateFinanceRecordError,
    GlValidationError,
    create_draft_journal,
)
from finance_service.services.posting import (
    PostingValidationError,
    post_journal,
)
from finance_service.services.year_close_rules import (
    FiscalYearCloseRuleError,
    validate_year_can_close,
)


class FiscalYearCloseWorkflowError(ValueError):
    pass


def _temporary_account_amounts(
    *,
    account_type: AccountType,
    closing_debit: Decimal,
    closing_credit: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    if account_type == AccountType.REVENUE:
        amount = closing_credit - closing_debit

        if amount <= 0:
            return Decimal("0"), Decimal("0"), Decimal("0")

        return amount, Decimal("0"), amount

    amount = closing_debit - closing_credit

    if amount <= 0:
        return Decimal("0"), Decimal("0"), Decimal("0")

    return Decimal("0"), amount, -amount


async def preview_fiscal_year_close(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
) -> FiscalYearClosePreview:
    fiscal_year = await get_fiscal_year_with_lock(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
    )

    if fiscal_year is None:
        raise FiscalYearCloseWorkflowError(
            "Fiscal year not found"
        )

    rows = await list_temporary_account_balances(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
    )

    revenue_total = Decimal("0")
    expense_total = Decimal("0")
    net_income = Decimal("0")
    lines: list[FiscalYearClosePreviewLine] = []

    account_totals: dict[
        UUID,
        dict[str, object],
    ] = {}

    for account, balance in rows:
        item = account_totals.setdefault(
            account.id,
            {
                "account": account,
                "debit": Decimal("0"),
                "credit": Decimal("0"),
            },
        )

        item["debit"] += balance.closing_debit
        item["credit"] += balance.closing_credit

    for item in account_totals.values():
        account = item["account"]
        closing_debit = item["debit"]
        closing_credit = item["credit"]

        debit, credit, income_effect = (
            _temporary_account_amounts(
                account_type=account.account_type,
                closing_debit=closing_debit,
                closing_credit=closing_credit,
            )
        )

        if debit == 0 and credit == 0:
            continue

        if account.account_type == AccountType.REVENUE:
            revenue_total += debit
        else:
            expense_total += credit

        net_income += income_effect

        lines.append(
            FiscalYearClosePreviewLine(
                ledger_account_id=account.id,
                account_code=account.code,
                account_name=account.name,
                debit=debit,
                credit=credit,
            )
        )

    return FiscalYearClosePreview(
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
        revenue_total=revenue_total,
        expense_total=expense_total,
        net_income=net_income,
        lines=lines,
    )


async def close_fiscal_year(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    fiscal_year_id: UUID,
    retained_earnings_account_id: UUID,
    started_by: UUID,
    closing_journal_number: str,
) -> FiscalYearCloseRun:
    fiscal_year = await get_fiscal_year_with_lock(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
    )

    if fiscal_year is None:
        raise FiscalYearCloseWorkflowError(
            "Fiscal year not found"
        )

    if fiscal_year.is_closed:
        raise FiscalYearCloseWorkflowError(
            "Fiscal year is already closed"
        )

    periods = await list_year_periods(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
    )

    current_run = await get_year_close_run(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
        for_update=True,
    )

    current_status = (
        current_run.status
        if current_run is not None
        else FiscalYearCloseStatus.OPEN
    )

    try:
        validate_year_can_close(
            period_statuses=[
                period.status for period in periods
            ],
            current_status=current_status,
        )
    except FiscalYearCloseRuleError as exc:
        raise FiscalYearCloseWorkflowError(
            str(exc)
        ) from exc

    retained_earnings = (
        await get_retained_earnings_account(
            session,
            tenant_id=tenant_id,
            account_id=retained_earnings_account_id,
        )
    )

    if retained_earnings is None:
        raise FiscalYearCloseWorkflowError(
            "Retained earnings equity account not found"
        )

    closing_period = await get_last_year_period(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
    )

    if closing_period is None:
        raise FiscalYearCloseWorkflowError(
            "Fiscal year has no closing period"
        )

    preview = await preview_fiscal_year_close(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
    )

    if current_run is None:
        current_run = FiscalYearCloseRun(
            tenant_id=tenant_id,
            fiscal_year_id=fiscal_year_id,
            retained_earnings_account_id=(
                retained_earnings_account_id
            ),
            status=FiscalYearCloseStatus.IN_PROGRESS,
            net_income=preview.net_income,
            started_by=started_by,
        )
        session.add(current_run)
        await session.flush()
    else:
        current_run.status = (
            FiscalYearCloseStatus.IN_PROGRESS
        )
        current_run.net_income = preview.net_income
        current_run.error_message = ""

    journal_lines: list[JournalLineCreate] = []
    line_number = 1

    for line in preview.lines:
        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=line.ledger_account_id,
                line_number=line_number,
                description="Fiscal-year closing entry",
                debit=line.debit,
                credit=line.credit,
            )
        )
        line_number += 1

    if preview.net_income > 0:
        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=retained_earnings.id,
                line_number=line_number,
                description="Transfer net income",
                credit=preview.net_income,
            )
        )
    elif preview.net_income < 0:
        journal_lines.append(
            JournalLineCreate(
                ledger_account_id=retained_earnings.id,
                line_number=line_number,
                description="Transfer net loss",
                debit=abs(preview.net_income),
            )
        )
    else:
        raise FiscalYearCloseWorkflowError(
            "Fiscal year has no temporary-account balance"
        )

    journal_payload = JournalEntryCreate(
        tenant_id=tenant_id,
        fiscal_period_id=closing_period.id,
        journal_number=closing_journal_number,
        entry_date=closing_period.ends_on,
        source=JournalSource.SYSTEM,
        source_reference=str(current_run.id),
        description=(
            f"Fiscal-year closing: {fiscal_year.name}"
        ),
        created_by=started_by,
        lines=journal_lines,
    )

    try:
        journal = await create_draft_journal(
            session,
            payload=journal_payload,
            allow_closed_period=True,
        )

        await post_journal(
            session,
            tenant_id=tenant_id,
            journal_id=journal.id,
            posted_by=started_by,
            allow_closed_period=True,
        )
    except (
        GlValidationError,
        DuplicateFinanceRecordError,
        PostingValidationError,
    ) as exc:
        current_run.status = FiscalYearCloseStatus.FAILED
        current_run.error_message = str(exc)[:1000]
        await session.commit()

        raise FiscalYearCloseWorkflowError(
            str(exc)
        ) from exc

    current_run = await get_year_close_run(
        session,
        tenant_id=tenant_id,
        fiscal_year_id=fiscal_year_id,
        for_update=True,
    )

    if current_run is None:
        raise FiscalYearCloseWorkflowError(
            "Fiscal-year close run disappeared"
        )

    current_run.closing_journal_id = journal.id
    current_run.status = FiscalYearCloseStatus.CLOSED
    current_run.completed_at = datetime.now(UTC)
    fiscal_year.is_closed = True

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise FiscalYearCloseWorkflowError(
            "Fiscal-year close already exists"
        ) from exc

    await session.refresh(current_run)
    return current_run

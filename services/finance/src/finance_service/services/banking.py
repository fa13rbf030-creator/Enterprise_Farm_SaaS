from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.enums import (
    AccountStatus,
    AccountType,
    BankAccountStatus,
    BankStatementLineType,
    BankStatementStatus,
    JournalSource,
    JournalStatus,
    ReconciliationMatchType,
    ReconciliationStatus,
)
from finance_service.models.banking import (
    BankAccount,
    BankReconciliation,
    BankReconciliationMatch,
    BankStatement,
    BankStatementLine,
)
from finance_service.repositories.banking import (
    get_bank_account,
    get_bank_statement,
    get_posted_journal,
    get_reconciliation,
    get_reconciliation_match_for_line,
    get_statement_line,
    list_bank_accounts,
    list_reconciliation_matches,
    list_statement_lines,
)
from finance_service.repositories.gl import (
    get_account,
    get_fiscal_period,
)
from finance_service.schemas.banking import (
    BankAccountCreate,
    BankAdjustmentCreate,
    BankStatementCreate,
    BankStatementDetailRead,
    BankStatementLineRead,
    CashPositionRead,
    DailyBankBalanceRead,
    ReconciliationCreate,
    ReconciliationDetailRead,
    ReconciliationMatchCreate,
    ReconciliationMatchRead,
)
from finance_service.schemas.gl import (
    JournalEntryCreate,
    JournalLineCreate,
)
from finance_service.services.banking_calculations import (
    BankingCalculationError,
    calculate_reconciliation_difference,
    calculate_statement_totals,
    quantize_bank_money,
    validate_match_amount,
)
from finance_service.services.gl import create_draft_journal
from finance_service.services.posting import post_journal


class BankingWorkflowError(ValueError):
    pass


async def _require_ledger_account(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    account_id: UUID,
    expected_type: AccountType | None = None,
):
    account = await get_account(
        session,
        tenant_id=tenant_id,
        account_id=account_id,
    )

    if account is None:
        raise BankingWorkflowError(
            "Ledger account not found in tenant"
        )

    if account.status != AccountStatus.ACTIVE:
        raise BankingWorkflowError(
            "Ledger account is not active"
        )

    if (
        expected_type is not None
        and account.account_type != expected_type
    ):
        raise BankingWorkflowError(
            f"Ledger account must be {expected_type.value}"
        )

    return account


async def create_bank_account(
    session: AsyncSession,
    *,
    payload: BankAccountCreate,
) -> BankAccount:
    await _require_ledger_account(
        session,
        tenant_id=payload.tenant_id,
        account_id=payload.ledger_account_id,
        expected_type=AccountType.ASSET,
    )

    account = BankAccount(
        tenant_id=payload.tenant_id,
        account_code=payload.account_code.strip(),
        account_name=payload.account_name.strip(),
        bank_name=payload.bank_name.strip(),
        branch_name=payload.branch_name.strip(),
        branch_code=payload.branch_code,
        account_number=payload.account_number.strip(),
        iban=(
            payload.iban.strip()
            if payload.iban
            else None
        ),
        swift_code=payload.swift_code,
        currency_code=payload.currency_code.upper(),
        account_type=payload.account_type,
        ledger_account_id=payload.ledger_account_id,
        opening_balance=payload.opening_balance,
        current_balance=payload.opening_balance,
        description=payload.description.strip(),
        created_by=payload.created_by,
    )

    session.add(account)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise BankingWorkflowError(
            "Bank account code or IBAN already exists"
        ) from exc

    await session.refresh(account)
    return account


async def import_bank_statement(
    session: AsyncSession,
    *,
    payload: BankStatementCreate,
) -> BankStatement:
    account = await get_bank_account(
        session,
        tenant_id=payload.tenant_id,
        bank_account_id=payload.bank_account_id,
    )

    if account is None:
        raise BankingWorkflowError(
            "Bank account not found"
        )

    if account.status != BankAccountStatus.ACTIVE:
        raise BankingWorkflowError(
            "Bank account is not active"
        )

    try:
        credits, debits, _closing = (
            calculate_statement_totals(payload)
        )
    except BankingCalculationError as exc:
        raise BankingWorkflowError(str(exc)) from exc

    statement = BankStatement(
        tenant_id=payload.tenant_id,
        bank_account_id=payload.bank_account_id,
        statement_number=(
            payload.statement_number.strip()
        ),
        statement_date=payload.statement_date,
        period_start=payload.period_start,
        period_end=payload.period_end,
        opening_balance=payload.opening_balance,
        closing_balance=payload.closing_balance,
        total_credits=credits,
        total_debits=debits,
        status=BankStatementStatus.IMPORTED,
        source_file_name=payload.source_file_name,
        imported_by=payload.imported_by,
    )

    session.add(statement)
    await session.flush()

    for line in payload.lines:
        session.add(
            BankStatementLine(
                tenant_id=payload.tenant_id,
                statement_id=statement.id,
                line_number=line.line_number,
                transaction_date=line.transaction_date,
                value_date=line.value_date,
                reference_number=line.reference_number,
                description=line.description.strip(),
                line_type=line.line_type,
                amount=line.amount,
                running_balance=line.running_balance,
            )
        )

    account.current_balance = payload.closing_balance

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise BankingWorkflowError(
            "Bank statement number or line number "
            "already exists"
        ) from exc

    await session.refresh(statement)
    return statement


async def get_bank_statement_detail(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    statement_id: UUID,
) -> BankStatementDetailRead:
    statement = await get_bank_statement(
        session,
        tenant_id=tenant_id,
        statement_id=statement_id,
    )

    if statement is None:
        raise BankingWorkflowError(
            "Bank statement not found"
        )

    lines = await list_statement_lines(
        session,
        tenant_id=tenant_id,
        statement_id=statement.id,
    )

    return BankStatementDetailRead(
        **statement.__dict__,
        lines=[
            BankStatementLineRead.model_validate(line)
            for line in lines
        ],
    )


async def create_reconciliation(
    session: AsyncSession,
    *,
    payload: ReconciliationCreate,
) -> BankReconciliation:
    account = await get_bank_account(
        session,
        tenant_id=payload.tenant_id,
        bank_account_id=payload.bank_account_id,
    )

    if account is None:
        raise BankingWorkflowError(
            "Bank account not found"
        )

    statement = await get_bank_statement(
        session,
        tenant_id=payload.tenant_id,
        statement_id=payload.statement_id,
        for_update=True,
    )

    if statement is None:
        raise BankingWorkflowError(
            "Bank statement not found"
        )

    if statement.bank_account_id != account.id:
        raise BankingWorkflowError(
            "Statement does not belong to bank account"
        )

    if statement.status not in {
        BankStatementStatus.IMPORTED,
        BankStatementStatus.IN_RECONCILIATION,
    }:
        raise BankingWorkflowError(
            "Bank statement cannot be reconciled"
        )

    difference = calculate_reconciliation_difference(
        book_balance=payload.book_balance,
        statement_balance=statement.closing_balance,
        reconciled_amount=Decimal("0"),
    )

    reconciliation = BankReconciliation(
        tenant_id=payload.tenant_id,
        bank_account_id=account.id,
        statement_id=statement.id,
        reconciliation_date=payload.reconciliation_date,
        book_balance=payload.book_balance,
        statement_balance=statement.closing_balance,
        reconciled_amount=Decimal("0"),
        difference_amount=difference,
        status=ReconciliationStatus.IN_PROGRESS,
        started_by=payload.started_by,
        notes=payload.notes.strip(),
    )

    session.add(reconciliation)
    statement.status = (
        BankStatementStatus.IN_RECONCILIATION
    )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise BankingWorkflowError(
            "Reconciliation already exists "
            "for this statement"
        ) from exc

    await session.refresh(reconciliation)
    return reconciliation


async def match_statement_line(
    session: AsyncSession,
    *,
    reconciliation_id: UUID,
    payload: ReconciliationMatchCreate,
) -> BankReconciliation:
    reconciliation = await get_reconciliation(
        session,
        tenant_id=payload.tenant_id,
        reconciliation_id=reconciliation_id,
        for_update=True,
    )

    if reconciliation is None:
        raise BankingWorkflowError(
            "Reconciliation not found"
        )

    if reconciliation.status != ReconciliationStatus.IN_PROGRESS:
        raise BankingWorkflowError(
            "Reconciliation is not in progress"
        )

    line = await get_statement_line(
        session,
        tenant_id=payload.tenant_id,
        statement_line_id=payload.statement_line_id,
        for_update=True,
    )

    if line is None:
        raise BankingWorkflowError(
            "Statement line not found"
        )

    if line.statement_id != reconciliation.statement_id:
        raise BankingWorkflowError(
            "Statement line does not belong "
            "to reconciliation statement"
        )

    existing = await get_reconciliation_match_for_line(
        session,
        tenant_id=payload.tenant_id,
        reconciliation_id=reconciliation.id,
        statement_line_id=line.id,
    )

    if existing is not None:
        raise BankingWorkflowError(
            "Statement line is already matched"
        )

    if payload.journal_entry_id is not None:
        journal = await get_posted_journal(
            session,
            tenant_id=payload.tenant_id,
            journal_entry_id=payload.journal_entry_id,
        )

        if journal is None:
            raise BankingWorkflowError(
                "Journal entry not found"
            )

        if journal.status not in {
            JournalStatus.POSTED,
            JournalStatus.REVERSED,
        }:
            raise BankingWorkflowError(
                "Only posted journals can be matched"
            )

    try:
        matched_total = validate_match_amount(
            statement_line_amount=line.amount,
            existing_matched_amount=Decimal("0"),
            new_matched_amount=payload.matched_amount,
        )
    except BankingCalculationError as exc:
        raise BankingWorkflowError(str(exc)) from exc

    session.add(
        BankReconciliationMatch(
            tenant_id=payload.tenant_id,
            reconciliation_id=reconciliation.id,
            statement_line_id=line.id,
            journal_entry_id=payload.journal_entry_id,
            match_type=payload.match_type,
            matched_amount=payload.matched_amount,
            matched_by=payload.matched_by,
        )
    )

    if matched_total == quantize_bank_money(line.amount):
        line.is_reconciled = True
        line.matched_journal_entry_id = (
            payload.journal_entry_id
        )

    reconciliation.reconciled_amount = (
        quantize_bank_money(
            reconciliation.reconciled_amount
            + payload.matched_amount
        )
    )
    reconciliation.difference_amount = (
        calculate_reconciliation_difference(
            book_balance=reconciliation.book_balance,
            statement_balance=(
                reconciliation.statement_balance
            ),
            reconciled_amount=(
                reconciliation.reconciled_amount
            ),
        )
    )

    await session.commit()
    await session.refresh(reconciliation)

    return reconciliation


async def post_bank_adjustment(
    session: AsyncSession,
    *,
    reconciliation_id: UUID,
    statement_line_id: UUID,
    payload: BankAdjustmentCreate,
    match_type: ReconciliationMatchType,
) -> BankReconciliation:
    if match_type not in {
        ReconciliationMatchType.BANK_CHARGE,
        ReconciliationMatchType.BANK_INTEREST,
    }:
        raise BankingWorkflowError(
            "Invalid bank-adjustment match type"
        )

    reconciliation = await get_reconciliation(
        session,
        tenant_id=payload.tenant_id,
        reconciliation_id=reconciliation_id,
    )

    if reconciliation is None:
        raise BankingWorkflowError(
            "Reconciliation not found"
        )

    line = await get_statement_line(
        session,
        tenant_id=payload.tenant_id,
        statement_line_id=statement_line_id,
    )

    if line is None:
        raise BankingWorkflowError(
            "Statement line not found"
        )

    account = await get_bank_account(
        session,
        tenant_id=payload.tenant_id,
        bank_account_id=reconciliation.bank_account_id,
    )

    if account is None:
        raise BankingWorkflowError(
            "Bank account not found"
        )

    period = await get_fiscal_period(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
    )

    if period is None:
        raise BankingWorkflowError(
            "Fiscal period not found"
        )

    if not (
        period.starts_on
        <= payload.transaction_date
        <= period.ends_on
    ):
        raise BankingWorkflowError(
            "Adjustment date is outside fiscal period"
        )

    await _require_ledger_account(
        session,
        tenant_id=payload.tenant_id,
        account_id=payload.offset_account_id,
    )

    if match_type == ReconciliationMatchType.BANK_CHARGE:
        if line.line_type != BankStatementLineType.DEBIT:
            raise BankingWorkflowError(
                "Bank charge requires a debit statement line"
            )

        journal_lines = [
            JournalLineCreate(
                ledger_account_id=payload.offset_account_id,
                line_number=1,
                description=payload.description,
                debit=line.amount,
            ),
            JournalLineCreate(
                ledger_account_id=account.ledger_account_id,
                line_number=2,
                description=payload.description,
                credit=line.amount,
            ),
        ]
    else:
        if line.line_type != BankStatementLineType.CREDIT:
            raise BankingWorkflowError(
                "Bank interest requires a credit statement line"
            )

        journal_lines = [
            JournalLineCreate(
                ledger_account_id=account.ledger_account_id,
                line_number=1,
                description=payload.description,
                debit=line.amount,
            ),
            JournalLineCreate(
                ledger_account_id=payload.offset_account_id,
                line_number=2,
                description=payload.description,
                credit=line.amount,
            ),
        ]

    journal = await create_draft_journal(
        session,
        payload=JournalEntryCreate(
            tenant_id=payload.tenant_id,
            fiscal_period_id=payload.fiscal_period_id,
            journal_number=payload.journal_number,
            entry_date=payload.transaction_date,
            source=JournalSource.BANK_RECONCILIATION,
            source_reference=str(line.id),
            description=payload.description,
            created_by=payload.posted_by,
            lines=journal_lines,
        ),
    )

    await post_journal(
        session,
        tenant_id=payload.tenant_id,
        journal_id=journal.id,
        posted_by=payload.posted_by,
    )

    return await match_statement_line(
        session,
        reconciliation_id=reconciliation_id,
        payload=ReconciliationMatchCreate(
            tenant_id=payload.tenant_id,
            statement_line_id=line.id,
            journal_entry_id=journal.id,
            match_type=match_type,
            matched_amount=line.amount,
            matched_by=payload.posted_by,
        ),
    )


async def complete_reconciliation(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    reconciliation_id: UUID,
    completed_by: UUID,
) -> BankReconciliation:
    reconciliation = await get_reconciliation(
        session,
        tenant_id=tenant_id,
        reconciliation_id=reconciliation_id,
        for_update=True,
    )

    if reconciliation is None:
        raise BankingWorkflowError(
            "Reconciliation not found"
        )

    if reconciliation.status != ReconciliationStatus.IN_PROGRESS:
        raise BankingWorkflowError(
            "Reconciliation is not in progress"
        )

    unmatched_lines = await list_statement_lines(
        session,
        tenant_id=tenant_id,
        statement_id=reconciliation.statement_id,
        unreconciled_only=True,
    )

    if unmatched_lines:
        raise BankingWorkflowError(
            "All statement lines must be reconciled"
        )

    if quantize_bank_money(
        reconciliation.difference_amount
    ) != Decimal("0.00"):
        raise BankingWorkflowError(
            "Reconciliation difference must be zero"
        )

    statement = await get_bank_statement(
        session,
        tenant_id=tenant_id,
        statement_id=reconciliation.statement_id,
        for_update=True,
    )

    if statement is None:
        raise BankingWorkflowError(
            "Bank statement not found"
        )

    account = await get_bank_account(
        session,
        tenant_id=tenant_id,
        bank_account_id=reconciliation.bank_account_id,
        for_update=True,
    )

    if account is None:
        raise BankingWorkflowError(
            "Bank account not found"
        )

    reconciliation.status = (
        ReconciliationStatus.COMPLETED
    )
    reconciliation.completed_by = completed_by
    reconciliation.completed_at = datetime.now(UTC)
    statement.status = BankStatementStatus.RECONCILED
    account.current_balance = statement.closing_balance

    await session.commit()
    await session.refresh(reconciliation)

    return reconciliation


async def get_reconciliation_detail(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    reconciliation_id: UUID,
) -> ReconciliationDetailRead:
    reconciliation = await get_reconciliation(
        session,
        tenant_id=tenant_id,
        reconciliation_id=reconciliation_id,
    )

    if reconciliation is None:
        raise BankingWorkflowError(
            "Reconciliation not found"
        )

    matches = await list_reconciliation_matches(
        session,
        tenant_id=tenant_id,
        reconciliation_id=reconciliation.id,
    )

    return ReconciliationDetailRead(
        **reconciliation.__dict__,
        matches=[
            ReconciliationMatchRead.model_validate(match)
            for match in matches
        ],
    )


async def build_cash_position(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    currency_code: str,
) -> CashPositionRead:
    accounts = await list_bank_accounts(
        session,
        tenant_id=tenant_id,
        currency_code=currency_code,
    )

    active_accounts = [
        account
        for account in accounts
        if account.status == BankAccountStatus.ACTIVE
    ]

    total = sum(
        (
            account.current_balance
            for account in active_accounts
        ),
        Decimal("0"),
    )

    return CashPositionRead(
        tenant_id=tenant_id,
        currency_code=currency_code.upper(),
        total_balance=quantize_bank_money(total),
        accounts=active_accounts,
    )


async def build_daily_bank_balance(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    bank_account_id: UUID,
    as_of_date: date,
) -> DailyBankBalanceRead:
    account = await get_bank_account(
        session,
        tenant_id=tenant_id,
        bank_account_id=bank_account_id,
    )

    if account is None:
        raise BankingWorkflowError(
            "Bank account not found"
        )

    credits = Decimal("0")
    debits = Decimal("0")

    statements = await session.execute(
        select(BankStatement).where(
            BankStatement.tenant_id == tenant_id,
            BankStatement.bank_account_id
            == bank_account_id,
            BankStatement.statement_date <= as_of_date,
        )
    )

    statement_ids = [
        statement.id
        for statement in statements.scalars().all()
    ]

    if statement_ids:
        lines_result = await session.execute(
            select(BankStatementLine).where(
                BankStatementLine.tenant_id == tenant_id,
                BankStatementLine.statement_id.in_(
                    statement_ids
                ),
                BankStatementLine.transaction_date
                <= as_of_date,
            )
        )

        for line in lines_result.scalars().all():
            if (
                line.line_type
                == BankStatementLineType.CREDIT
            ):
                credits += line.amount
            else:
                debits += line.amount

    closing = quantize_bank_money(
        account.opening_balance + credits - debits
    )

    return DailyBankBalanceRead(
        tenant_id=tenant_id,
        bank_account_id=bank_account_id,
        as_of_date=as_of_date,
        opening_balance=account.opening_balance,
        credits=quantize_bank_money(credits),
        debits=quantize_bank_money(debits),
        closing_balance=closing,
    )

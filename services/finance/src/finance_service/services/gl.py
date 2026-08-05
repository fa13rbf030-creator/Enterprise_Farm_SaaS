from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from finance_service.core.config import get_settings
from finance_service.core.enums import (
    AccountStatus,
    FiscalPeriodStatus,
)
from finance_service.models.gl import (
    FiscalPeriod,
    FiscalYear,
    JournalEntry,
    JournalLine,
    LedgerAccount,
)
from finance_service.repositories.gl import (
    get_account,
    get_fiscal_period,
    get_fiscal_year,
)
from finance_service.schemas.gl import (
    FiscalPeriodCreate,
    FiscalYearCreate,
    JournalEntryCreate,
    LedgerAccountCreate,
)
from finance_service.services.gl_validation import (
    JournalValidationError,
    calculate_base_amount,
    validate_balanced_journal,
)


class GlValidationError(ValueError):
    pass


class DuplicateFinanceRecordError(ValueError):
    pass


async def create_ledger_account(
    session: AsyncSession,
    *,
    payload: LedgerAccountCreate,
) -> LedgerAccount:
    if payload.parent_id is not None:
        parent = await get_account(
            session,
            tenant_id=payload.tenant_id,
            account_id=payload.parent_id,
        )

        if parent is None:
            raise GlValidationError(
                "Parent account not found in tenant"
            )

    account = LedgerAccount(
        tenant_id=payload.tenant_id,
        parent_id=payload.parent_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        description=payload.description.strip(),
        account_type=payload.account_type,
        normal_balance=payload.normal_balance,
        currency_code=payload.currency_code.upper(),
        is_control_account=payload.is_control_account,
        allows_manual_posting=(
            payload.allows_manual_posting
        ),
    )

    session.add(account)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateFinanceRecordError(
            "Ledger account code already exists in tenant"
        ) from exc

    await session.refresh(account)
    return account


async def create_fiscal_year(
    session: AsyncSession,
    *,
    payload: FiscalYearCreate,
) -> FiscalYear:
    fiscal_year = FiscalYear(
        tenant_id=payload.tenant_id,
        name=payload.name.strip(),
        starts_on=payload.starts_on,
        ends_on=payload.ends_on,
    )

    session.add(fiscal_year)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateFinanceRecordError(
            "Fiscal year already exists in tenant"
        ) from exc

    await session.refresh(fiscal_year)
    return fiscal_year


async def create_fiscal_period(
    session: AsyncSession,
    *,
    payload: FiscalPeriodCreate,
) -> FiscalPeriod:
    fiscal_year = await get_fiscal_year(
        session,
        tenant_id=payload.tenant_id,
        fiscal_year_id=payload.fiscal_year_id,
    )

    if fiscal_year is None:
        raise GlValidationError(
            "Fiscal year not found in tenant"
        )

    if (
        payload.starts_on < fiscal_year.starts_on
        or payload.ends_on > fiscal_year.ends_on
    ):
        raise GlValidationError(
            "Fiscal period must fall within fiscal year"
        )

    period = FiscalPeriod(
        tenant_id=payload.tenant_id,
        fiscal_year_id=payload.fiscal_year_id,
        period_number=payload.period_number,
        name=payload.name.strip(),
        starts_on=payload.starts_on,
        ends_on=payload.ends_on,
    )

    session.add(period)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateFinanceRecordError(
            "Fiscal period number already exists"
        ) from exc

    await session.refresh(period)
    return period


async def create_draft_journal(
    session: AsyncSession,
    *,
    payload: JournalEntryCreate,
) -> JournalEntry:
    period = await get_fiscal_period(
        session,
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
    )

    if period is None:
        raise GlValidationError(
            "Fiscal period not found in tenant"
        )

    if period.status != FiscalPeriodStatus.OPEN:
        raise GlValidationError(
            "Journal can only be created in an open period"
        )

    if not (
        period.starts_on
        <= payload.entry_date
        <= period.ends_on
    ):
        raise GlValidationError(
            "Journal date is outside fiscal period"
        )

    account_ids = {
        line.ledger_account_id
        for line in payload.lines
    }

    accounts: dict[UUID, LedgerAccount] = {}

    for account_id in account_ids:
        account = await get_account(
            session,
            tenant_id=payload.tenant_id,
            account_id=account_id,
        )

        if account is None:
            raise GlValidationError(
                "Journal account not found in tenant"
            )

        if account.status != AccountStatus.ACTIVE:
            raise GlValidationError(
                "Journal account is not active"
            )

        if (
            payload.source.value == "manual"
            and not account.allows_manual_posting
        ):
            raise GlValidationError(
                "Account does not allow manual posting"
            )

        accounts[account_id] = account

    settings = get_settings()

    try:
        total_debit, total_credit = (
            validate_balanced_journal(
                payload,
                decimal_places=settings.decimal_places,
            )
        )
    except JournalValidationError as exc:
        raise GlValidationError(str(exc)) from exc

    journal = JournalEntry(
        tenant_id=payload.tenant_id,
        fiscal_period_id=payload.fiscal_period_id,
        journal_number=payload.journal_number.strip(),
        entry_date=payload.entry_date,
        source=payload.source,
        source_reference=payload.source_reference,
        description=payload.description.strip(),
        total_debit=total_debit,
        total_credit=total_credit,
        created_by=payload.created_by,
    )

    session.add(journal)
    await session.flush()

    for line in payload.lines:
        session.add(
            JournalLine(
                tenant_id=payload.tenant_id,
                journal_entry_id=journal.id,
                ledger_account_id=line.ledger_account_id,
                line_number=line.line_number,
                description=line.description.strip(),
                debit=line.debit,
                credit=line.credit,
                currency_code=(
                    line.currency_code.upper()
                ),
                exchange_rate=line.exchange_rate,
                base_debit=calculate_base_amount(
                    line.debit,
                    line.exchange_rate,
                    decimal_places=(
                        settings.decimal_places
                    ),
                ),
                base_credit=calculate_base_amount(
                    line.credit,
                    line.exchange_rate,
                    decimal_places=(
                        settings.decimal_places
                    ),
                ),
            )
        )

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateFinanceRecordError(
            "Journal number already exists in tenant"
        ) from exc

    await session.refresh(journal)
    return journal

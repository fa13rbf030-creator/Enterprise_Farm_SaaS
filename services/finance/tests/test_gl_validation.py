from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from finance_service.schemas.gl import (
    JournalEntryCreate,
    JournalLineCreate,
)
from finance_service.services.gl_validation import (
    JournalValidationError,
    calculate_base_amount,
    validate_balanced_journal,
)


def build_journal(
    *,
    debit: Decimal = Decimal("100"),
    credit: Decimal = Decimal("100"),
) -> JournalEntryCreate:
    return JournalEntryCreate(
        tenant_id=uuid4(),
        fiscal_period_id=uuid4(),
        journal_number="JV-0001",
        entry_date=date(2026, 8, 5),
        description="Opening journal",
        created_by=uuid4(),
        lines=[
            JournalLineCreate(
                ledger_account_id=uuid4(),
                line_number=1,
                debit=debit,
            ),
            JournalLineCreate(
                ledger_account_id=uuid4(),
                line_number=2,
                credit=credit,
            ),
        ],
    )


def test_balanced_journal_is_valid() -> None:
    journal = build_journal()

    debit, credit = validate_balanced_journal(
        journal
    )

    assert debit == Decimal("100.00")
    assert credit == Decimal("100.00")


def test_unbalanced_journal_is_rejected() -> None:
    journal = build_journal(
        debit=Decimal("100"),
        credit=Decimal("90"),
    )

    with pytest.raises(
        JournalValidationError,
        match="not balanced",
    ):
        validate_balanced_journal(journal)


def test_duplicate_line_numbers_are_rejected() -> None:
    journal = build_journal()
    journal.lines[1].line_number = 1

    with pytest.raises(
        JournalValidationError,
        match="must be unique",
    ):
        validate_balanced_journal(journal)


def test_exchange_rate_calculates_base_amount() -> None:
    assert calculate_base_amount(
        Decimal("10"),
        Decimal("279.5"),
    ) == Decimal("2795.00")


def test_line_cannot_have_debit_and_credit() -> None:
    with pytest.raises(
        ValueError,
        match="both debit and credit",
    ):
        JournalLineCreate(
            ledger_account_id=uuid4(),
            line_number=1,
            debit=Decimal("10"),
            credit=Decimal("10"),
        )

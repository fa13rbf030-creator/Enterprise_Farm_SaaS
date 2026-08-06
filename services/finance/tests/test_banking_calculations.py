from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from finance_service.core.enums import (
    BankStatementLineType,
)
from finance_service.schemas.banking import (
    BankStatementCreate,
    BankStatementLineCreate,
)
from finance_service.services.banking_calculations import (
    BankingCalculationError,
    calculate_reconciliation_difference,
    calculate_statement_totals,
    validate_match_amount,
)


def build_statement() -> BankStatementCreate:
    return BankStatementCreate(
        tenant_id=uuid4(),
        bank_account_id=uuid4(),
        statement_number="ST-001",
        statement_date=date(2026, 1, 31),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        opening_balance=Decimal("1000"),
        closing_balance=Decimal("1250"),
        imported_by=uuid4(),
        lines=[
            BankStatementLineCreate(
                line_number=1,
                transaction_date=date(2026, 1, 5),
                description="Customer receipt",
                line_type=BankStatementLineType.CREDIT,
                amount=Decimal("500"),
            ),
            BankStatementLineCreate(
                line_number=2,
                transaction_date=date(2026, 1, 10),
                description="Vendor payment",
                line_type=BankStatementLineType.DEBIT,
                amount=Decimal("250"),
            ),
        ],
    )


def test_statement_totals() -> None:
    credits, debits, closing = (
        calculate_statement_totals(build_statement())
    )

    assert credits == Decimal("500.00")
    assert debits == Decimal("250.00")
    assert closing == Decimal("1250.00")


def test_invalid_statement_closing_balance() -> None:
    payload = build_statement()
    payload.closing_balance = Decimal("1200")

    with pytest.raises(
        BankingCalculationError,
        match="closing balance",
    ):
        calculate_statement_totals(payload)


def test_reconciliation_difference() -> None:
    assert calculate_reconciliation_difference(
        book_balance=Decimal("1200"),
        statement_balance=Decimal("1250"),
        reconciled_amount=Decimal("50"),
    ) == Decimal("0.00")


def test_match_overallocation_rejected() -> None:
    with pytest.raises(BankingCalculationError):
        validate_match_amount(
            statement_line_amount=Decimal("100"),
            existing_matched_amount=Decimal("80"),
            new_matched_amount=Decimal("30"),
        )

from decimal import Decimal

from finance_service.core.enums import AccountType
from finance_service.services.year_close import (
    _temporary_account_amounts,
)


def test_revenue_close_amount() -> None:
    debit, credit, income = _temporary_account_amounts(
        account_type=AccountType.REVENUE,
        closing_debit=Decimal("0"),
        closing_credit=Decimal("100"),
    )

    assert debit == Decimal("100")
    assert credit == Decimal("0")
    assert income == Decimal("100")


def test_expense_close_amount() -> None:
    debit, credit, income = _temporary_account_amounts(
        account_type=AccountType.EXPENSE,
        closing_debit=Decimal("40"),
        closing_credit=Decimal("0"),
    )

    assert debit == Decimal("0")
    assert credit == Decimal("40")
    assert income == Decimal("-40")


def test_zero_temporary_balance() -> None:
    debit, credit, income = _temporary_account_amounts(
        account_type=AccountType.REVENUE,
        closing_debit=Decimal("100"),
        closing_credit=Decimal("100"),
    )

    assert debit == Decimal("0")
    assert credit == Decimal("0")
    assert income == Decimal("0")

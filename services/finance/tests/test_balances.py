from decimal import Decimal

from finance_service.core.enums import (
    BalanceDirection,
    NormalBalance,
)
from finance_service.services.balances import (
    calculate_net_balance,
    determine_balance_direction,
)


def test_debit_normal_account_balance() -> None:
    debit, credit = calculate_net_balance(
        debit=Decimal("100"),
        credit=Decimal("25"),
        normal_balance=NormalBalance.DEBIT,
    )

    assert debit == Decimal("75")
    assert credit == Decimal("0")


def test_credit_normal_account_balance() -> None:
    debit, credit = calculate_net_balance(
        debit=Decimal("25"),
        credit=Decimal("100"),
        normal_balance=NormalBalance.CREDIT,
    )

    assert debit == Decimal("0")
    assert credit == Decimal("75")


def test_balance_direction() -> None:
    assert determine_balance_direction(
        debit=Decimal("50"),
        credit=Decimal("20"),
    ) == BalanceDirection.DEBIT

    assert determine_balance_direction(
        debit=Decimal("20"),
        credit=Decimal("50"),
    ) == BalanceDirection.CREDIT

    assert determine_balance_direction(
        debit=Decimal("50"),
        credit=Decimal("50"),
    ) == BalanceDirection.ZERO

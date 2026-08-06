from decimal import Decimal

import pytest

from finance_service.services.intercompany_calculations import (
    IntercompanyCalculationError,
    calculate_base_amount,
    calculate_elimination_amount,
    calculate_intercompany_difference,
    calculate_non_controlling_interest,
    calculate_ownership_share,
    calculate_translated_amount,
    is_intercompany_match,
)


def test_base_amount_calculation() -> None:
    assert calculate_base_amount(
        transaction_amount=Decimal("1000"),
        exchange_rate=Decimal("280"),
    ) == Decimal("280000.00")


def test_translated_amount() -> None:
    assert calculate_translated_amount(
        source_amount=Decimal("1000"),
        translation_rate=Decimal("278.50"),
    ) == Decimal("278500.00")


def test_ownership_share() -> None:
    assert calculate_ownership_share(
        amount=Decimal("1000000"),
        ownership_percentage=Decimal("75"),
    ) == Decimal("750000.00")


def test_intercompany_difference() -> None:
    assert calculate_intercompany_difference(
        source_balance=Decimal("500000"),
        destination_balance=Decimal("499999.50"),
    ) == Decimal("0.50")


def test_balances_match_within_tolerance() -> None:
    assert is_intercompany_match(
        source_balance=Decimal("1000.00"),
        destination_balance=Decimal("999.99"),
        tolerance=Decimal("0.01"),
    ) is True


def test_elimination_amount_uses_lower_balance() -> None:
    assert calculate_elimination_amount(
        source_balance=Decimal("100000"),
        counterparty_balance=Decimal("95000"),
    ) == Decimal("95000.00")


def test_non_controlling_interest() -> None:
    assert calculate_non_controlling_interest(
        subsidiary_net_assets=Decimal("1000000"),
        parent_ownership_percentage=Decimal("80"),
    ) == Decimal("200000.00")


def test_invalid_ownership_percentage() -> None:
    with pytest.raises(IntercompanyCalculationError):
        calculate_ownership_share(
            amount=Decimal("1000"),
            ownership_percentage=Decimal("101"),
        )

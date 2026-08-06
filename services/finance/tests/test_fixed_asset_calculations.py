from decimal import Decimal

import pytest

from finance_service.services.fixed_asset_calculations import (
    FixedAssetCalculationError,
    calculate_depreciable_amount,
    calculate_disposal_gain_loss,
    calculate_reducing_balance_depreciation,
    calculate_revaluation_surplus,
    calculate_straight_line_depreciation,
    calculate_units_of_production_depreciation,
)


def test_depreciable_amount() -> None:
    assert calculate_depreciable_amount(
        acquisition_cost=Decimal("100000"),
        residual_value=Decimal("10000"),
    ) == Decimal("90000.00")


def test_straight_line_monthly_depreciation() -> None:
    assert calculate_straight_line_depreciation(
        acquisition_cost=Decimal("100000"),
        residual_value=Decimal("10000"),
        useful_life_months=60,
    ) == Decimal("1500.00")


def test_reducing_balance_depreciation() -> None:
    result = calculate_reducing_balance_depreciation(
        opening_net_book_value=Decimal("100000"),
        annual_rate_percent=Decimal("20"),
        months=1,
    )

    assert result == Decimal("1666.67")


def test_units_of_production_depreciation() -> None:
    result = calculate_units_of_production_depreciation(
        acquisition_cost=Decimal("110000"),
        residual_value=Decimal("10000"),
        estimated_total_units=Decimal("100000"),
        units_consumed=Decimal("5000"),
    )

    assert result == Decimal("5000.00")


def test_disposal_gain() -> None:
    result = calculate_disposal_gain_loss(
        disposal_proceeds=Decimal("50000"),
        net_book_value=Decimal("42000"),
        disposal_costs=Decimal("1000"),
    )

    assert result == Decimal("7000.00")


def test_revaluation_surplus() -> None:
    assert calculate_revaluation_surplus(
        current_net_book_value=Decimal("80000"),
        revalued_amount=Decimal("95000"),
    ) == Decimal("15000.00")


def test_invalid_residual_value() -> None:
    with pytest.raises(FixedAssetCalculationError):
        calculate_depreciable_amount(
            acquisition_cost=Decimal("100"),
            residual_value=Decimal("101"),
        )

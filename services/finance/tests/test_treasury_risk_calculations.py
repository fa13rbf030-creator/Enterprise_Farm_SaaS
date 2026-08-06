from decimal import Decimal

import pytest

from finance_service.services.treasury_risk_calculations import (
    TreasuryRiskCalculationError,
    calculate_expected_investment_value,
    calculate_fx_exposure,
    calculate_intercompany_transfer,
    calculate_stressed_liquidity,
)


def test_fx_exposure_calculation() -> None:
    base, unhedged = calculate_fx_exposure(
        foreign_amount=Decimal("100000"),
        spot_rate=Decimal("280"),
        hedged_amount=Decimal("40000"),
    )

    assert base == Decimal("28000000.00")
    assert unhedged == Decimal("60000.00")


def test_invalid_hedge_amount_rejected() -> None:
    with pytest.raises(TreasuryRiskCalculationError):
        calculate_fx_exposure(
            foreign_amount=Decimal("100"),
            spot_rate=Decimal("280"),
            hedged_amount=Decimal("101"),
        )


def test_intercompany_transfer_conversion() -> None:
    assert calculate_intercompany_transfer(
        source_amount=Decimal("1000"),
        exchange_rate=Decimal("280"),
    ) == Decimal("280000.00")


def test_expected_investment_value() -> None:
    value = calculate_expected_investment_value(
        principal=Decimal("1000000"),
        annual_rate_percent=Decimal("12"),
        term_days=365,
    )

    assert value == Decimal("1120000.00")


def test_stressed_liquidity_shortfall() -> None:
    liquidity, shortfall = calculate_stressed_liquidity(
        opening_liquidity=Decimal("1000000"),
        expected_inflows=Decimal("500000"),
        expected_outflows=Decimal("1200000"),
        inflow_reduction_percent=Decimal("50"),
        outflow_increase_percent=Decimal("25"),
        minimum_buffer=Decimal("300000"),
    )

    assert liquidity == Decimal("-250000.00")
    assert shortfall == Decimal("550000.00")

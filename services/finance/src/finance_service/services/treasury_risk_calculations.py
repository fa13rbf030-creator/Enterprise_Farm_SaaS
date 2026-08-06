from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class TreasuryRiskCalculationError(ValueError):
    pass


def quantize_risk_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_fx_exposure(
    *,
    foreign_amount: Decimal,
    spot_rate: Decimal,
    hedged_amount: Decimal = Decimal("0"),
) -> tuple[Decimal, Decimal]:
    if foreign_amount <= 0:
        raise TreasuryRiskCalculationError(
            "Foreign amount must be positive"
        )

    if spot_rate <= 0:
        raise TreasuryRiskCalculationError(
            "Spot rate must be positive"
        )

    if hedged_amount < 0 or hedged_amount > foreign_amount:
        raise TreasuryRiskCalculationError(
            "Hedged amount is outside exposure range"
        )

    base_amount = quantize_risk_money(
        foreign_amount * spot_rate
    )
    unhedged_amount = quantize_risk_money(
        foreign_amount - hedged_amount
    )

    return base_amount, unhedged_amount


def calculate_intercompany_transfer(
    *,
    source_amount: Decimal,
    exchange_rate: Decimal,
) -> Decimal:
    if source_amount <= 0 or exchange_rate <= 0:
        raise TreasuryRiskCalculationError(
            "Transfer amount and exchange rate must be positive"
        )

    return quantize_risk_money(
        source_amount * exchange_rate
    )


def calculate_expected_investment_value(
    *,
    principal: Decimal,
    annual_rate_percent: Decimal,
    term_days: int,
) -> Decimal:
    if principal <= 0:
        raise TreasuryRiskCalculationError(
            "Investment principal must be positive"
        )

    if term_days <= 0:
        raise TreasuryRiskCalculationError(
            "Investment term must be positive"
        )

    return quantize_risk_money(
        principal
        * (
            Decimal("1")
            + (
                annual_rate_percent
                / Decimal("100")
                * Decimal(term_days)
                / Decimal("365")
            )
        )
    )


def calculate_stressed_liquidity(
    *,
    opening_liquidity: Decimal,
    expected_inflows: Decimal,
    expected_outflows: Decimal,
    inflow_reduction_percent: Decimal,
    outflow_increase_percent: Decimal,
    minimum_buffer: Decimal,
) -> tuple[Decimal, Decimal]:
    stressed_inflows = expected_inflows * (
        Decimal("1")
        - inflow_reduction_percent / Decimal("100")
    )

    stressed_outflows = expected_outflows * (
        Decimal("1")
        + outflow_increase_percent / Decimal("100")
    )

    stressed_liquidity = quantize_risk_money(
        opening_liquidity
        + stressed_inflows
        - stressed_outflows
    )

    shortfall = quantize_risk_money(
        max(
            minimum_buffer - stressed_liquidity,
            Decimal("0"),
        )
    )

    return stressed_liquidity, shortfall

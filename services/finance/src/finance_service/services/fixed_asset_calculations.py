from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class FixedAssetCalculationError(ValueError):
    pass


def quantize_asset_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_depreciable_amount(
    *,
    acquisition_cost: Decimal,
    residual_value: Decimal,
) -> Decimal:
    if acquisition_cost < 0:
        raise FixedAssetCalculationError(
            "Acquisition cost cannot be negative"
        )

    if residual_value < 0:
        raise FixedAssetCalculationError(
            "Residual value cannot be negative"
        )

    if residual_value > acquisition_cost:
        raise FixedAssetCalculationError(
            "Residual value cannot exceed acquisition cost"
        )

    return quantize_asset_money(
        acquisition_cost - residual_value
    )


def calculate_straight_line_depreciation(
    *,
    acquisition_cost: Decimal,
    residual_value: Decimal,
    useful_life_months: int,
) -> Decimal:
    if useful_life_months <= 0:
        raise FixedAssetCalculationError(
            "Useful life must be positive"
        )

    depreciable_amount = calculate_depreciable_amount(
        acquisition_cost=acquisition_cost,
        residual_value=residual_value,
    )

    return quantize_asset_money(
        depreciable_amount / Decimal(useful_life_months)
    )


def calculate_reducing_balance_depreciation(
    *,
    opening_net_book_value: Decimal,
    annual_rate_percent: Decimal,
    months: int = 1,
    residual_value: Decimal = Decimal("0"),
) -> Decimal:
    if opening_net_book_value < 0:
        raise FixedAssetCalculationError(
            "Opening net book value cannot be negative"
        )

    if annual_rate_percent < 0:
        raise FixedAssetCalculationError(
            "Annual depreciation rate cannot be negative"
        )

    if months <= 0 or months > 12:
        raise FixedAssetCalculationError(
            "Months must be between 1 and 12"
        )

    depreciation = (
        opening_net_book_value
        * annual_rate_percent
        / Decimal("100")
        * Decimal(months)
        / Decimal("12")
    )

    maximum_depreciation = max(
        opening_net_book_value - residual_value,
        Decimal("0"),
    )

    return quantize_asset_money(
        min(depreciation, maximum_depreciation)
    )


def calculate_units_of_production_depreciation(
    *,
    acquisition_cost: Decimal,
    residual_value: Decimal,
    estimated_total_units: Decimal,
    units_consumed: Decimal,
) -> Decimal:
    if estimated_total_units <= 0:
        raise FixedAssetCalculationError(
            "Estimated production units must be positive"
        )

    if units_consumed < 0:
        raise FixedAssetCalculationError(
            "Consumed units cannot be negative"
        )

    depreciable_amount = calculate_depreciable_amount(
        acquisition_cost=acquisition_cost,
        residual_value=residual_value,
    )

    depreciation = (
        depreciable_amount
        * units_consumed
        / estimated_total_units
    )

    return quantize_asset_money(
        min(depreciation, depreciable_amount)
    )


def calculate_disposal_gain_loss(
    *,
    disposal_proceeds: Decimal,
    net_book_value: Decimal,
    disposal_costs: Decimal = Decimal("0"),
) -> Decimal:
    if disposal_proceeds < 0:
        raise FixedAssetCalculationError(
            "Disposal proceeds cannot be negative"
        )

    if net_book_value < 0:
        raise FixedAssetCalculationError(
            "Net book value cannot be negative"
        )

    if disposal_costs < 0:
        raise FixedAssetCalculationError(
            "Disposal costs cannot be negative"
        )

    return quantize_asset_money(
        disposal_proceeds
        - disposal_costs
        - net_book_value
    )


def calculate_revaluation_surplus(
    *,
    current_net_book_value: Decimal,
    revalued_amount: Decimal,
) -> Decimal:
    if current_net_book_value < 0 or revalued_amount < 0:
        raise FixedAssetCalculationError(
            "Asset values cannot be negative"
        )

    return quantize_asset_money(
        revalued_amount - current_net_book_value
    )

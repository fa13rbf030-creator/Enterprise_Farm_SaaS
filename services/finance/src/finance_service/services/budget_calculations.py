from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class BudgetCalculationError(ValueError):
    pass


def quantize_budget_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_budget_line_amount(
    *,
    quantity: Decimal,
    unit_rate: Decimal,
) -> Decimal:
    if quantity < 0:
        raise BudgetCalculationError(
            "Budget quantity cannot be negative"
        )

    if unit_rate < 0:
        raise BudgetCalculationError(
            "Budget unit rate cannot be negative"
        )

    return quantize_budget_money(quantity * unit_rate)


def calculate_budget_variance(
    *,
    budget_amount: Decimal,
    actual_amount: Decimal,
    expense_nature: bool = True,
) -> tuple[Decimal, Decimal, bool]:
    variance = quantize_budget_money(
        actual_amount - budget_amount
    )

    if budget_amount == 0:
        variance_percent = Decimal("0.00")
    else:
        variance_percent = quantize_budget_money(
            variance / budget_amount * Decimal("100")
        )

    favourable = (
        variance <= 0
        if expense_nature
        else variance >= 0
    )

    return variance, variance_percent, favourable


def calculate_standard_cost(
    *,
    material_cost: Decimal,
    labour_cost: Decimal,
    overhead_cost: Decimal,
) -> Decimal:
    components = (
        material_cost,
        labour_cost,
        overhead_cost,
    )

    if any(value < 0 for value in components):
        raise BudgetCalculationError(
            "Standard-cost components cannot be negative"
        )

    return quantize_budget_money(sum(components))


def calculate_allocation_amounts(
    *,
    source_amount: Decimal,
    percentages: list[Decimal],
) -> list[Decimal]:
    if source_amount < 0:
        raise BudgetCalculationError(
            "Source amount cannot be negative"
        )

    if not percentages:
        raise BudgetCalculationError(
            "At least one allocation percentage is required"
        )

    total_percentage = sum(percentages)

    if total_percentage != Decimal("100"):
        raise BudgetCalculationError(
            "Allocation percentages must total 100"
        )

    results = [
        quantize_budget_money(
            source_amount
            * percentage
            / Decimal("100")
        )
        for percentage in percentages
    ]

    rounding_difference = (
        quantize_budget_money(source_amount)
        - sum(results)
    )

    results[-1] += rounding_difference
    return results

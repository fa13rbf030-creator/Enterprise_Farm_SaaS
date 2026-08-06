from decimal import Decimal

import pytest

from finance_service.services.budget_calculations import (
    BudgetCalculationError,
    calculate_allocation_amounts,
    calculate_budget_line_amount,
    calculate_budget_variance,
    calculate_standard_cost,
)


def test_budget_line_amount() -> None:
    assert calculate_budget_line_amount(
        quantity=Decimal("100"),
        unit_rate=Decimal("25.50"),
    ) == Decimal("2550.00")


def test_expense_variance() -> None:
    variance, percent, favourable = calculate_budget_variance(
        budget_amount=Decimal("1000"),
        actual_amount=Decimal("900"),
        expense_nature=True,
    )

    assert variance == Decimal("-100.00")
    assert percent == Decimal("-10.00")
    assert favourable is True


def test_revenue_variance() -> None:
    variance, _percent, favourable = calculate_budget_variance(
        budget_amount=Decimal("1000"),
        actual_amount=Decimal("1200"),
        expense_nature=False,
    )

    assert variance == Decimal("200.00")
    assert favourable is True


def test_standard_cost() -> None:
    assert calculate_standard_cost(
        material_cost=Decimal("100"),
        labour_cost=Decimal("50"),
        overhead_cost=Decimal("25"),
    ) == Decimal("175.00")


def test_allocation_percentages() -> None:
    allocations = calculate_allocation_amounts(
        source_amount=Decimal("1000"),
        percentages=[
            Decimal("50"),
            Decimal("30"),
            Decimal("20"),
        ],
    )

    assert allocations == [
        Decimal("500.00"),
        Decimal("300.00"),
        Decimal("200.00"),
    ]


def test_invalid_allocation_total() -> None:
    with pytest.raises(BudgetCalculationError):
        calculate_allocation_amounts(
            source_amount=Decimal("1000"),
            percentages=[
                Decimal("60"),
                Decimal("30"),
            ],
        )

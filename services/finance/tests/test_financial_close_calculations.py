from decimal import Decimal

import pytest

from finance_service.services.financial_close_calculations import (
    FinancialCloseCalculationError,
    calculate_close_completion_percentage,
    calculate_close_variance,
    calculate_close_variance_percentage,
    calculate_materiality_threshold,
    calculate_trial_balance_difference,
    calculate_unreconciled_difference,
    is_exception_material,
    is_trial_balance_balanced,
)


def test_trial_balance_difference() -> None:
    assert calculate_trial_balance_difference(
        total_debits=Decimal("100000"),
        total_credits=Decimal("99999.50"),
    ) == Decimal("0.50")


def test_trial_balance_balanced_with_tolerance() -> None:
    assert is_trial_balance_balanced(
        total_debits=Decimal("1000.00"),
        total_credits=Decimal("999.99"),
        tolerance=Decimal("0.01"),
    ) is True


def test_close_completion_percentage() -> None:
    assert calculate_close_completion_percentage(
        completed_tasks=9,
        total_tasks=12,
    ) == Decimal("75.00")


def test_zero_task_completion() -> None:
    assert calculate_close_completion_percentage(
        completed_tasks=0,
        total_tasks=0,
    ) == Decimal("0.00")


def test_unreconciled_difference() -> None:
    assert calculate_unreconciled_difference(
        ledger_balance=Decimal("250000"),
        subledger_balance=Decimal("249500"),
    ) == Decimal("500.00")


def test_materiality_threshold() -> None:
    assert calculate_materiality_threshold(
        benchmark_amount=Decimal("10000000"),
        percentage=Decimal("1"),
    ) == Decimal("100000.00")


def test_exception_is_material() -> None:
    assert is_exception_material(
        exception_amount=Decimal("-150000"),
        materiality_threshold=Decimal("100000"),
    ) is True


def test_close_variance() -> None:
    assert calculate_close_variance(
        current_period_amount=Decimal("120000"),
        prior_period_amount=Decimal("100000"),
    ) == Decimal("20000.00")


def test_close_variance_percentage() -> None:
    assert calculate_close_variance_percentage(
        current_period_amount=Decimal("120000"),
        prior_period_amount=Decimal("100000"),
    ) == Decimal("20.00")


def test_zero_prior_period_returns_none() -> None:
    assert calculate_close_variance_percentage(
        current_period_amount=Decimal("100"),
        prior_period_amount=Decimal("0"),
    ) is None


def test_invalid_completed_task_count() -> None:
    with pytest.raises(FinancialCloseCalculationError):
        calculate_close_completion_percentage(
            completed_tasks=11,
            total_tasks=10,
        )

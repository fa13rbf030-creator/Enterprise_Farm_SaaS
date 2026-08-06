from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class FinancialCloseCalculationError(ValueError):
    pass


def quantize_close_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_trial_balance_difference(
    *,
    total_debits: Decimal,
    total_credits: Decimal,
) -> Decimal:
    if total_debits < 0 or total_credits < 0:
        raise FinancialCloseCalculationError(
            "Trial-balance totals cannot be negative"
        )

    return quantize_close_money(
        total_debits - total_credits
    )


def is_trial_balance_balanced(
    *,
    total_debits: Decimal,
    total_credits: Decimal,
    tolerance: Decimal = Decimal("0.01"),
) -> bool:
    if tolerance < 0:
        raise FinancialCloseCalculationError(
            "Tolerance cannot be negative"
        )

    difference = calculate_trial_balance_difference(
        total_debits=total_debits,
        total_credits=total_credits,
    )

    return abs(difference) <= tolerance


def calculate_close_completion_percentage(
    *,
    completed_tasks: int,
    total_tasks: int,
) -> Decimal:
    if total_tasks < 0 or completed_tasks < 0:
        raise FinancialCloseCalculationError(
            "Task counts cannot be negative"
        )

    if completed_tasks > total_tasks:
        raise FinancialCloseCalculationError(
            "Completed tasks cannot exceed total tasks"
        )

    if total_tasks == 0:
        return Decimal("0.00")

    return quantize_close_money(
        Decimal(completed_tasks)
        * Decimal("100")
        / Decimal(total_tasks)
    )


def calculate_unreconciled_difference(
    *,
    ledger_balance: Decimal,
    subledger_balance: Decimal,
) -> Decimal:
    return quantize_close_money(
        ledger_balance - subledger_balance
    )


def calculate_materiality_threshold(
    *,
    benchmark_amount: Decimal,
    percentage: Decimal,
) -> Decimal:
    if benchmark_amount < 0:
        raise FinancialCloseCalculationError(
            "Benchmark amount cannot be negative"
        )

    if percentage < 0 or percentage > 100:
        raise FinancialCloseCalculationError(
            "Percentage must be between 0 and 100"
        )

    return quantize_close_money(
        benchmark_amount
        * percentage
        / Decimal("100")
    )


def is_exception_material(
    *,
    exception_amount: Decimal,
    materiality_threshold: Decimal,
) -> bool:
    if materiality_threshold < 0:
        raise FinancialCloseCalculationError(
            "Materiality threshold cannot be negative"
        )

    return abs(exception_amount) >= materiality_threshold


def calculate_close_variance(
    *,
    current_period_amount: Decimal,
    prior_period_amount: Decimal,
) -> Decimal:
    return quantize_close_money(
        current_period_amount - prior_period_amount
    )


def calculate_close_variance_percentage(
    *,
    current_period_amount: Decimal,
    prior_period_amount: Decimal,
) -> Decimal | None:
    if prior_period_amount == 0:
        return None

    return quantize_close_money(
        (
            current_period_amount
            - prior_period_amount
        )
        * Decimal("100")
        / abs(prior_period_amount)
    )

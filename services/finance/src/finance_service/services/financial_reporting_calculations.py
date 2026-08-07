from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class FinancialReportingCalculationError(ValueError):
    pass


def quantize_report_money(
    value: Decimal,
) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_net_balance(
    *,
    debit_amount: Decimal,
    credit_amount: Decimal,
    debit_normal: bool,
) -> Decimal:
    if debit_amount < 0 or credit_amount < 0:
        raise FinancialReportingCalculationError(
            "Debit and credit amounts cannot be negative"
        )

    if debit_normal:
        return quantize_report_money(
            debit_amount - credit_amount
        )

    return quantize_report_money(
        credit_amount - debit_amount
    )


def calculate_statement_total(
    amounts: list[Decimal],
) -> Decimal:
    return quantize_report_money(
        sum(amounts, Decimal("0"))
    )


def calculate_gross_profit(
    *,
    revenue: Decimal,
    cost_of_sales: Decimal,
) -> Decimal:
    return quantize_report_money(
        revenue - cost_of_sales
    )


def calculate_operating_profit(
    *,
    gross_profit: Decimal,
    operating_expenses: Decimal,
    other_operating_income: Decimal = Decimal("0"),
) -> Decimal:
    return quantize_report_money(
        gross_profit
        + other_operating_income
        - operating_expenses
    )


def calculate_net_profit(
    *,
    operating_profit: Decimal,
    finance_costs: Decimal,
    tax_expense: Decimal,
    non_operating_income: Decimal = Decimal("0"),
) -> Decimal:
    return quantize_report_money(
        operating_profit
        + non_operating_income
        - finance_costs
        - tax_expense
    )


def calculate_working_capital(
    *,
    current_assets: Decimal,
    current_liabilities: Decimal,
) -> Decimal:
    return quantize_report_money(
        current_assets - current_liabilities
    )


def calculate_current_ratio(
    *,
    current_assets: Decimal,
    current_liabilities: Decimal,
) -> Decimal | None:
    if current_liabilities == 0:
        return None

    return (
        current_assets / current_liabilities
    ).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )


def calculate_budget_variance(
    *,
    actual_amount: Decimal,
    budget_amount: Decimal,
) -> Decimal:
    return quantize_report_money(
        actual_amount - budget_amount
    )


def calculate_budget_variance_percentage(
    *,
    actual_amount: Decimal,
    budget_amount: Decimal,
) -> Decimal | None:
    if budget_amount == 0:
        return None

    return (
        (actual_amount - budget_amount)
        * Decimal("100")
        / abs(budget_amount)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_period_change(
    *,
    current_amount: Decimal,
    comparative_amount: Decimal,
) -> Decimal:
    return quantize_report_money(
        current_amount - comparative_amount
    )


def calculate_period_change_percentage(
    *,
    current_amount: Decimal,
    comparative_amount: Decimal,
) -> Decimal | None:
    if comparative_amount == 0:
        return None

    return (
        (current_amount - comparative_amount)
        * Decimal("100")
        / abs(comparative_amount)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_cash_flow_total(
    *,
    operating_cash_flow: Decimal,
    investing_cash_flow: Decimal,
    financing_cash_flow: Decimal,
) -> Decimal:
    return quantize_report_money(
        operating_cash_flow
        + investing_cash_flow
        + financing_cash_flow
    )


def calculate_closing_cash(
    *,
    opening_cash: Decimal,
    net_cash_flow: Decimal,
    fx_effect: Decimal = Decimal("0"),
) -> Decimal:
    return quantize_report_money(
        opening_cash
        + net_cash_flow
        + fx_effect
    )


def calculate_ending_equity(
    *,
    opening_equity: Decimal,
    net_profit: Decimal,
    owner_contributions: Decimal = Decimal("0"),
    dividends: Decimal = Decimal("0"),
    other_comprehensive_income: Decimal = Decimal("0"),
) -> Decimal:
    return quantize_report_money(
        opening_equity
        + net_profit
        + owner_contributions
        - dividends
        + other_comprehensive_income
    )

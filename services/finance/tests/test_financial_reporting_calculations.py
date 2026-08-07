from decimal import Decimal

import pytest

from finance_service.services.financial_reporting_calculations import (
    FinancialReportingCalculationError,
    calculate_budget_variance,
    calculate_budget_variance_percentage,
    calculate_cash_flow_total,
    calculate_closing_cash,
    calculate_current_ratio,
    calculate_ending_equity,
    calculate_gross_profit,
    calculate_net_balance,
    calculate_net_profit,
    calculate_operating_profit,
    calculate_period_change,
    calculate_period_change_percentage,
    calculate_statement_total,
    calculate_working_capital,
)


def test_debit_normal_net_balance() -> None:
    assert calculate_net_balance(
        debit_amount=Decimal("1000"),
        credit_amount=Decimal("250"),
        debit_normal=True,
    ) == Decimal("750.00")


def test_credit_normal_net_balance() -> None:
    assert calculate_net_balance(
        debit_amount=Decimal("100"),
        credit_amount=Decimal("600"),
        debit_normal=False,
    ) == Decimal("500.00")


def test_statement_total() -> None:
    assert calculate_statement_total(
        [
            Decimal("100"),
            Decimal("200.25"),
            Decimal("-50"),
        ]
    ) == Decimal("250.25")


def test_gross_profit() -> None:
    assert calculate_gross_profit(
        revenue=Decimal("1000000"),
        cost_of_sales=Decimal("600000"),
    ) == Decimal("400000.00")


def test_operating_profit() -> None:
    assert calculate_operating_profit(
        gross_profit=Decimal("400000"),
        operating_expenses=Decimal("250000"),
        other_operating_income=Decimal("10000"),
    ) == Decimal("160000.00")


def test_net_profit() -> None:
    assert calculate_net_profit(
        operating_profit=Decimal("160000"),
        finance_costs=Decimal("20000"),
        tax_expense=Decimal("30000"),
        non_operating_income=Decimal("5000"),
    ) == Decimal("115000.00")


def test_working_capital() -> None:
    assert calculate_working_capital(
        current_assets=Decimal("900000"),
        current_liabilities=Decimal("350000"),
    ) == Decimal("550000.00")


def test_current_ratio() -> None:
    assert calculate_current_ratio(
        current_assets=Decimal("900000"),
        current_liabilities=Decimal("300000"),
    ) == Decimal("3.0000")


def test_zero_liability_ratio_returns_none() -> None:
    assert calculate_current_ratio(
        current_assets=Decimal("100"),
        current_liabilities=Decimal("0"),
    ) is None


def test_budget_variance() -> None:
    assert calculate_budget_variance(
        actual_amount=Decimal("120000"),
        budget_amount=Decimal("100000"),
    ) == Decimal("20000.00")


def test_budget_variance_percentage() -> None:
    assert calculate_budget_variance_percentage(
        actual_amount=Decimal("120000"),
        budget_amount=Decimal("100000"),
    ) == Decimal("20.00")


def test_period_change() -> None:
    assert calculate_period_change(
        current_amount=Decimal("150000"),
        comparative_amount=Decimal("125000"),
    ) == Decimal("25000.00")


def test_period_change_percentage() -> None:
    assert calculate_period_change_percentage(
        current_amount=Decimal("150000"),
        comparative_amount=Decimal("125000"),
    ) == Decimal("20.00")


def test_cash_flow_total() -> None:
    assert calculate_cash_flow_total(
        operating_cash_flow=Decimal("500000"),
        investing_cash_flow=Decimal("-200000"),
        financing_cash_flow=Decimal("-100000"),
    ) == Decimal("200000.00")


def test_closing_cash() -> None:
    assert calculate_closing_cash(
        opening_cash=Decimal("300000"),
        net_cash_flow=Decimal("200000"),
        fx_effect=Decimal("-5000"),
    ) == Decimal("495000.00")


def test_ending_equity() -> None:
    assert calculate_ending_equity(
        opening_equity=Decimal("1000000"),
        net_profit=Decimal("250000"),
        owner_contributions=Decimal("50000"),
        dividends=Decimal("100000"),
        other_comprehensive_income=Decimal("10000"),
    ) == Decimal("1210000.00")


def test_negative_ledger_amount_rejected() -> None:
    with pytest.raises(
        FinancialReportingCalculationError
    ):
        calculate_net_balance(
            debit_amount=Decimal("-1"),
            credit_amount=Decimal("0"),
            debit_normal=True,
        )

from decimal import Decimal

from finance_service.services.finance_analytics_calculations import (
    calculate_budget_utilization_percentage,
    calculate_cash_conversion_cycle,
    calculate_debt_to_equity_ratio,
    calculate_dpo,
    calculate_dso,
    calculate_ebitda,
    calculate_ebitda_margin_percentage,
    calculate_free_cash_flow,
    calculate_gross_margin_percentage,
    calculate_inventory_days,
    calculate_net_margin_percentage,
    calculate_operating_margin_percentage,
    calculate_quick_ratio,
    calculate_return_on_assets_percentage,
    calculate_return_on_equity_percentage,
    calculate_working_capital,
)


def test_quick_ratio() -> None:
    assert calculate_quick_ratio(
        cash_and_equivalents=Decimal("100"),
        marketable_securities=Decimal("50"),
        accounts_receivable=Decimal("150"),
        current_liabilities=Decimal("200"),
    ) == Decimal("1.500000")


def test_quick_ratio_zero_liabilities() -> None:
    assert calculate_quick_ratio(
        cash_and_equivalents=Decimal("100"),
        marketable_securities=Decimal("0"),
        accounts_receivable=Decimal("50"),
        current_liabilities=Decimal("0"),
    ) is None


def test_profitability_margins() -> None:
    assert calculate_gross_margin_percentage(
        revenue=Decimal("1000"),
        cost_of_goods_sold=Decimal("600"),
    ) == Decimal("40.00")

    assert calculate_operating_margin_percentage(
        revenue=Decimal("1000"),
        operating_income=Decimal("250"),
    ) == Decimal("25.00")

    assert calculate_net_margin_percentage(
        revenue=Decimal("1000"),
        net_income=Decimal("180"),
    ) == Decimal("18.00")


def test_ebitda_and_margin() -> None:
    ebitda = calculate_ebitda(
        net_income=Decimal("100"),
        interest_expense=Decimal("20"),
        tax_expense=Decimal("30"),
        depreciation=Decimal("40"),
        amortization=Decimal("10"),
    )

    assert ebitda == Decimal("200.000000")

    assert calculate_ebitda_margin_percentage(
        revenue=Decimal("1000"),
        ebitda=ebitda,
    ) == Decimal("20.00")


def test_returns_and_leverage() -> None:
    assert calculate_return_on_assets_percentage(
        net_income=Decimal("100"),
        average_total_assets=Decimal("1000"),
    ) == Decimal("10.00")

    assert calculate_return_on_equity_percentage(
        net_income=Decimal("100"),
        average_equity=Decimal("500"),
    ) == Decimal("20.00")

    assert calculate_debt_to_equity_ratio(
        total_debt=Decimal("300"),
        total_equity=Decimal("500"),
    ) == Decimal("0.600000")


def test_dso_dpo_inventory_days_and_ccc() -> None:
    dso = calculate_dso(
        average_accounts_receivable=Decimal("120"),
        credit_sales=Decimal("1200"),
        days_in_period=365,
    )

    dpo = calculate_dpo(
        average_accounts_payable=Decimal("90"),
        credit_purchases=Decimal("900"),
        days_in_period=365,
    )

    inventory_days = calculate_inventory_days(
        average_inventory=Decimal("200"),
        cost_of_goods_sold=Decimal("1000"),
        days_in_period=365,
    )

    assert dso == Decimal("36.50")
    assert dpo == Decimal("36.50")
    assert inventory_days == Decimal("73.00")

    assert calculate_cash_conversion_cycle(
        inventory_days=inventory_days,
        dso=dso,
        dpo=dpo,
    ) == Decimal("73.00")


def test_working_capital_and_free_cash_flow() -> None:
    assert calculate_working_capital(
        current_assets=Decimal("900"),
        current_liabilities=Decimal("500"),
    ) == Decimal("400.000000")

    assert calculate_free_cash_flow(
        operating_cash_flow=Decimal("700"),
        capital_expenditure=Decimal("250"),
    ) == Decimal("450.000000")


def test_budget_utilization() -> None:
    assert calculate_budget_utilization_percentage(
        actual_amount=Decimal("750"),
        budget_amount=Decimal("1000"),
    ) == Decimal("75.00")

    assert calculate_budget_utilization_percentage(
        actual_amount=Decimal("10"),
        budget_amount=Decimal("0"),
    ) is None


def test_zero_denominators_return_none() -> None:
    assert calculate_dso(
        average_accounts_receivable=Decimal("100"),
        credit_sales=Decimal("0"),
        days_in_period=365,
    ) is None

    assert calculate_dpo(
        average_accounts_payable=Decimal("100"),
        credit_purchases=Decimal("0"),
        days_in_period=365,
    ) is None

    assert calculate_inventory_days(
        average_inventory=Decimal("100"),
        cost_of_goods_sold=Decimal("0"),
        days_in_period=365,
    ) is None

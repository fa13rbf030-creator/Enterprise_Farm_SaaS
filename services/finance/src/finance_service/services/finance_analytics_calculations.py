from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


MONEY_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
PERCENT_QUANTUM = Decimal("0.01")
DAYS_QUANTUM = Decimal("0.01")


def _decimal(value: Decimal | int | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def quantize_money(value: Decimal | int | str) -> Decimal:
    return _decimal(value).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def quantize_ratio(value: Decimal | int | str) -> Decimal:
    return _decimal(value).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def quantize_percent(value: Decimal | int | str) -> Decimal:
    return _decimal(value).quantize(
        PERCENT_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def quantize_days(value: Decimal | int | str) -> Decimal:
    return _decimal(value).quantize(
        DAYS_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def safe_ratio(
    numerator: Decimal,
    denominator: Decimal,
) -> Decimal | None:
    numerator = _decimal(numerator)
    denominator = _decimal(denominator)

    if denominator == 0:
        return None

    return quantize_ratio(numerator / denominator)


def calculate_quick_ratio(
    *,
    cash_and_equivalents: Decimal,
    marketable_securities: Decimal,
    accounts_receivable: Decimal,
    current_liabilities: Decimal,
) -> Decimal | None:
    quick_assets = (
        _decimal(cash_and_equivalents)
        + _decimal(marketable_securities)
        + _decimal(accounts_receivable)
    )

    return safe_ratio(
        quick_assets,
        _decimal(current_liabilities),
    )


def calculate_gross_margin_percentage(
    *,
    revenue: Decimal,
    cost_of_goods_sold: Decimal,
) -> Decimal | None:
    revenue = _decimal(revenue)

    if revenue == 0:
        return None

    gross_profit = revenue - _decimal(cost_of_goods_sold)

    return quantize_percent(
        (gross_profit / revenue) * Decimal("100")
    )


def calculate_operating_margin_percentage(
    *,
    revenue: Decimal,
    operating_income: Decimal,
) -> Decimal | None:
    revenue = _decimal(revenue)

    if revenue == 0:
        return None

    return quantize_percent(
        (_decimal(operating_income) / revenue)
        * Decimal("100")
    )


def calculate_net_margin_percentage(
    *,
    revenue: Decimal,
    net_income: Decimal,
) -> Decimal | None:
    revenue = _decimal(revenue)

    if revenue == 0:
        return None

    return quantize_percent(
        (_decimal(net_income) / revenue)
        * Decimal("100")
    )


def calculate_ebitda(
    *,
    net_income: Decimal,
    interest_expense: Decimal,
    tax_expense: Decimal,
    depreciation: Decimal,
    amortization: Decimal,
) -> Decimal:
    return quantize_money(
        _decimal(net_income)
        + _decimal(interest_expense)
        + _decimal(tax_expense)
        + _decimal(depreciation)
        + _decimal(amortization)
    )


def calculate_ebitda_margin_percentage(
    *,
    revenue: Decimal,
    ebitda: Decimal,
) -> Decimal | None:
    revenue = _decimal(revenue)

    if revenue == 0:
        return None

    return quantize_percent(
        (_decimal(ebitda) / revenue)
        * Decimal("100")
    )


def calculate_return_on_assets_percentage(
    *,
    net_income: Decimal,
    average_total_assets: Decimal,
) -> Decimal | None:
    assets = _decimal(average_total_assets)

    if assets == 0:
        return None

    return quantize_percent(
        (_decimal(net_income) / assets)
        * Decimal("100")
    )


def calculate_return_on_equity_percentage(
    *,
    net_income: Decimal,
    average_equity: Decimal,
) -> Decimal | None:
    equity = _decimal(average_equity)

    if equity == 0:
        return None

    return quantize_percent(
        (_decimal(net_income) / equity)
        * Decimal("100")
    )


def calculate_debt_to_equity_ratio(
    *,
    total_debt: Decimal,
    total_equity: Decimal,
) -> Decimal | None:
    return safe_ratio(
        _decimal(total_debt),
        _decimal(total_equity),
    )


def calculate_dso(
    *,
    average_accounts_receivable: Decimal,
    credit_sales: Decimal,
    days_in_period: int,
) -> Decimal | None:
    sales = _decimal(credit_sales)

    if sales == 0 or days_in_period <= 0:
        return None

    return quantize_days(
        (
            _decimal(average_accounts_receivable)
            / sales
        )
        * Decimal(days_in_period)
    )


def calculate_dpo(
    *,
    average_accounts_payable: Decimal,
    credit_purchases: Decimal,
    days_in_period: int,
) -> Decimal | None:
    purchases = _decimal(credit_purchases)

    if purchases == 0 or days_in_period <= 0:
        return None

    return quantize_days(
        (
            _decimal(average_accounts_payable)
            / purchases
        )
        * Decimal(days_in_period)
    )


def calculate_inventory_days(
    *,
    average_inventory: Decimal,
    cost_of_goods_sold: Decimal,
    days_in_period: int,
) -> Decimal | None:
    cogs = _decimal(cost_of_goods_sold)

    if cogs == 0 or days_in_period <= 0:
        return None

    return quantize_days(
        (
            _decimal(average_inventory)
            / cogs
        )
        * Decimal(days_in_period)
    )


def calculate_cash_conversion_cycle(
    *,
    inventory_days: Decimal,
    dso: Decimal,
    dpo: Decimal,
) -> Decimal:
    return quantize_days(
        _decimal(inventory_days)
        + _decimal(dso)
        - _decimal(dpo)
    )


def calculate_working_capital(
    *,
    current_assets: Decimal,
    current_liabilities: Decimal,
) -> Decimal:
    return quantize_money(
        _decimal(current_assets)
        - _decimal(current_liabilities)
    )


def calculate_free_cash_flow(
    *,
    operating_cash_flow: Decimal,
    capital_expenditure: Decimal,
) -> Decimal:
    return quantize_money(
        _decimal(operating_cash_flow)
        - _decimal(capital_expenditure)
    )


def calculate_budget_utilization_percentage(
    *,
    actual_amount: Decimal,
    budget_amount: Decimal,
) -> Decimal | None:
    budget = _decimal(budget_amount)

    if budget == 0:
        return None

    return quantize_percent(
        (_decimal(actual_amount) / budget)
        * Decimal("100")
    )

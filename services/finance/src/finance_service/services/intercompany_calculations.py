from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class IntercompanyCalculationError(ValueError):
    pass


def quantize_intercompany_money(
    value: Decimal,
) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_base_amount(
    *,
    transaction_amount: Decimal,
    exchange_rate: Decimal,
) -> Decimal:
    if transaction_amount <= 0:
        raise IntercompanyCalculationError(
            "Transaction amount must be positive"
        )

    if exchange_rate <= 0:
        raise IntercompanyCalculationError(
            "Exchange rate must be positive"
        )

    return quantize_intercompany_money(
        transaction_amount * exchange_rate
    )


def calculate_translated_amount(
    *,
    source_amount: Decimal,
    translation_rate: Decimal,
) -> Decimal:
    if translation_rate <= 0:
        raise IntercompanyCalculationError(
            "Translation rate must be positive"
        )

    return quantize_intercompany_money(
        source_amount * translation_rate
    )


def calculate_ownership_share(
    *,
    amount: Decimal,
    ownership_percentage: Decimal,
) -> Decimal:
    if (
        ownership_percentage < 0
        or ownership_percentage > 100
    ):
        raise IntercompanyCalculationError(
            "Ownership percentage must be between 0 and 100"
        )

    return quantize_intercompany_money(
        amount
        * ownership_percentage
        / Decimal("100")
    )


def calculate_intercompany_difference(
    *,
    source_balance: Decimal,
    destination_balance: Decimal,
) -> Decimal:
    return quantize_intercompany_money(
        source_balance - destination_balance
    )


def is_intercompany_match(
    *,
    source_balance: Decimal,
    destination_balance: Decimal,
    tolerance: Decimal = Decimal("0.01"),
) -> bool:
    if tolerance < 0:
        raise IntercompanyCalculationError(
            "Tolerance cannot be negative"
        )

    difference = abs(
        source_balance - destination_balance
    )

    return difference <= tolerance


def calculate_elimination_amount(
    *,
    source_balance: Decimal,
    counterparty_balance: Decimal,
) -> Decimal:
    if source_balance < 0 or counterparty_balance < 0:
        raise IntercompanyCalculationError(
            "Elimination balances cannot be negative"
        )

    return quantize_intercompany_money(
        min(source_balance, counterparty_balance)
    )


def calculate_non_controlling_interest(
    *,
    subsidiary_net_assets: Decimal,
    parent_ownership_percentage: Decimal,
) -> Decimal:
    if (
        parent_ownership_percentage < 0
        or parent_ownership_percentage > 100
    ):
        raise IntercompanyCalculationError(
            "Parent ownership percentage must be between 0 and 100"
        )

    non_controlling_percentage = (
        Decimal("100")
        - parent_ownership_percentage
    )

    return quantize_intercompany_money(
        subsidiary_net_assets
        * non_controlling_percentage
        / Decimal("100")
    )

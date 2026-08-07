from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


MONEY_QUANTUM = Decimal("0.01")
RATE_DIVISOR = Decimal("100")


def quantize_tax_money(value: Decimal) -> Decimal:
    return value.quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def calculate_percentage_tax(
    taxable_amount: Decimal,
    rate: Decimal,
) -> Decimal:
    if taxable_amount < 0:
        raise ValueError(
            "Taxable amount cannot be negative"
        )

    if rate < 0 or rate > 100:
        raise ValueError(
            "Tax rate must be between 0 and 100"
        )

    return quantize_tax_money(
        taxable_amount * rate / RATE_DIVISOR
    )


def calculate_withholding_tax(
    taxable_amount: Decimal,
    rate: Decimal,
) -> Decimal:
    return calculate_percentage_tax(
        taxable_amount,
        rate,
    )


def calculate_net_tax_liability(
    *,
    output_tax: Decimal,
    input_tax: Decimal,
    adjustments: Decimal = Decimal("0"),
    credits: Decimal = Decimal("0"),
) -> Decimal:
    for name, value in (
        ("output_tax", output_tax),
        ("input_tax", input_tax),
        ("credits", credits),
    ):
        if value < 0:
            raise ValueError(
                f"{name} cannot be negative"
            )

    return quantize_tax_money(
        output_tax
        - input_tax
        + adjustments
        - credits
    )


def calculate_return_variance(
    *,
    ledger_amount: Decimal,
    return_amount: Decimal,
) -> Decimal:
    return quantize_tax_money(
        ledger_amount - return_amount
    )


def calculate_effective_tax_rate(
    *,
    tax_amount: Decimal,
    taxable_amount: Decimal,
) -> Decimal:
    if taxable_amount < 0:
        raise ValueError(
            "Taxable amount cannot be negative"
        )

    if taxable_amount == 0:
        return Decimal("0.00")

    return (
        tax_amount
        * RATE_DIVISOR
        / taxable_amount
    ).quantize(
        MONEY_QUANTUM,
        rounding=ROUND_HALF_UP,
    )

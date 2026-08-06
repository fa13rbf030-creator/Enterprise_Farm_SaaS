from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from finance_service.schemas.ar import (
    AgingBucket,
    InvoiceCreate,
)


class ArCalculationError(ValueError):
    pass


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_invoice_totals(
    payload: InvoiceCreate,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    tax_total = Decimal("0")

    line_numbers: set[int] = set()

    for line in payload.lines:
        if line.line_number in line_numbers:
            raise ArCalculationError(
                "Invoice line numbers must be unique"
            )

        line_numbers.add(line.line_number)

        gross = quantize_money(
            line.quantity * line.unit_price
        )

        if line.discount_amount > gross:
            raise ArCalculationError(
                "Invoice-line discount exceeds gross amount"
            )

        taxable = gross - line.discount_amount
        tax = quantize_money(
            taxable * line.tax_rate / Decimal("100")
        )

        subtotal += gross
        discount_total += line.discount_amount
        tax_total += tax

    subtotal = quantize_money(subtotal)
    discount_total = quantize_money(discount_total)
    tax_total = quantize_money(tax_total)

    total = quantize_money(
        subtotal - discount_total + tax_total
    )

    if total <= 0:
        raise ArCalculationError(
            "Invoice total must be greater than zero"
        )

    return (
        subtotal,
        discount_total,
        tax_total,
        total,
    )


def calculate_outstanding_amount(
    *,
    total_amount: Decimal,
    paid_amount: Decimal,
    credited_amount: Decimal,
) -> Decimal:
    outstanding = quantize_money(
        total_amount - paid_amount - credited_amount
    )

    if outstanding < 0:
        raise ArCalculationError(
            "Invoice allocations exceed invoice total"
        )

    return outstanding


def calculate_aging_bucket(
    *,
    as_of_date: date,
    due_date: date,
    outstanding_amount: Decimal,
) -> AgingBucket:
    amount = quantize_money(outstanding_amount)
    days_overdue = (as_of_date - due_date).days

    values = {
        "current": Decimal("0"),
        "days_1_30": Decimal("0"),
        "days_31_60": Decimal("0"),
        "days_61_90": Decimal("0"),
        "over_90": Decimal("0"),
    }

    if days_overdue <= 0:
        values["current"] = amount
    elif days_overdue <= 30:
        values["days_1_30"] = amount
    elif days_overdue <= 60:
        values["days_31_60"] = amount
    elif days_overdue <= 90:
        values["days_61_90"] = amount
    else:
        values["over_90"] = amount

    return AgingBucket(
        **values,
        total=amount,
    )

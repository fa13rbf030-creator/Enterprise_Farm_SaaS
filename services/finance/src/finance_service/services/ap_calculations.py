from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from finance_service.schemas.ap import (
    PayablesAgingRead,
    SupplierInvoiceCreate,
)


class ApCalculationError(ValueError):
    pass


def quantize_ap_money(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def calculate_supplier_invoice_totals(
    payload: SupplierInvoiceCreate,
) -> tuple[
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
]:
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    tax_total = Decimal("0")
    withholding_total = Decimal("0")
    line_numbers: set[int] = set()

    for line in payload.lines:
        if line.line_number in line_numbers:
            raise ApCalculationError(
                "Supplier invoice line numbers must be unique"
            )

        line_numbers.add(line.line_number)

        gross = quantize_ap_money(
            line.quantity * line.unit_price
        )

        if line.discount_amount > gross:
            raise ApCalculationError(
                "Supplier invoice discount exceeds gross amount"
            )

        taxable = gross - line.discount_amount

        tax_amount = quantize_ap_money(
            taxable
            * line.tax_rate
            / Decimal("100")
        )

        withholding_amount = quantize_ap_money(
            taxable
            * line.withholding_tax_rate
            / Decimal("100")
        )

        subtotal += gross
        discount_total += line.discount_amount
        tax_total += tax_amount
        withholding_total += withholding_amount

    subtotal = quantize_ap_money(subtotal)
    discount_total = quantize_ap_money(discount_total)
    tax_total = quantize_ap_money(tax_total)
    withholding_total = quantize_ap_money(
        withholding_total
    )

    total_amount = quantize_ap_money(
        subtotal
        - discount_total
        + tax_total
        - withholding_total
    )

    if total_amount <= 0:
        raise ApCalculationError(
            "Supplier invoice total must be greater than zero"
        )

    return (
        subtotal,
        discount_total,
        tax_total,
        withholding_total,
        total_amount,
    )


def calculate_payable_outstanding(
    *,
    total_amount: Decimal,
    paid_amount: Decimal,
    debited_amount: Decimal,
) -> Decimal:
    outstanding = quantize_ap_money(
        total_amount - paid_amount - debited_amount
    )

    if outstanding < 0:
        raise ApCalculationError(
            "Supplier invoice settlements exceed total"
        )

    return outstanding


def calculate_payables_aging(
    *,
    tenant_id,
    vendor_id,
    as_of_date: date,
    due_date: date,
    outstanding_amount: Decimal,
) -> PayablesAgingRead:
    amount = quantize_ap_money(outstanding_amount)
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

    return PayablesAgingRead(
        tenant_id=tenant_id,
        vendor_id=vendor_id,
        as_of_date=as_of_date,
        **values,
        total=amount,
    )

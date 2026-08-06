from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from finance_service.schemas.ar import (
    InvoiceCreate,
    InvoiceLineCreate,
)
from finance_service.services.ar_calculations import (
    ArCalculationError,
    calculate_aging_bucket,
    calculate_invoice_totals,
    calculate_outstanding_amount,
)


def build_invoice() -> InvoiceCreate:
    return InvoiceCreate(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        fiscal_period_id=uuid4(),
        invoice_number="INV-001",
        invoice_date=date(2026, 1, 1),
        due_date=date(2026, 1, 31),
        created_by=uuid4(),
        lines=[
            InvoiceLineCreate(
                line_number=1,
                description="Milk sale",
                quantity=Decimal("10"),
                unit_price=Decimal("100"),
                discount_amount=Decimal("100"),
                tax_rate=Decimal("10"),
                revenue_account_id=uuid4(),
            )
        ],
    )


def test_invoice_totals() -> None:
    subtotal, discount, tax, total = (
        calculate_invoice_totals(build_invoice())
    )

    assert subtotal == Decimal("1000.00")
    assert discount == Decimal("100.00")
    assert tax == Decimal("90.00")
    assert total == Decimal("990.00")


def test_outstanding_amount() -> None:
    assert calculate_outstanding_amount(
        total_amount=Decimal("1000"),
        paid_amount=Decimal("300"),
        credited_amount=Decimal("100"),
    ) == Decimal("600.00")


def test_overallocation_rejected() -> None:
    with pytest.raises(ArCalculationError):
        calculate_outstanding_amount(
            total_amount=Decimal("100"),
            paid_amount=Decimal("90"),
            credited_amount=Decimal("20"),
        )


def test_aging_bucket() -> None:
    aging = calculate_aging_bucket(
        as_of_date=date(2026, 4, 15),
        due_date=date(2026, 1, 1),
        outstanding_amount=Decimal("500"),
    )

    assert aging.over_90 == Decimal("500.00")
    assert aging.total == Decimal("500.00")

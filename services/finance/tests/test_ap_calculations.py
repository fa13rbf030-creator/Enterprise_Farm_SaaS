from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from finance_service.schemas.ap import (
    SupplierInvoiceCreate,
    SupplierInvoiceLineCreate,
)
from finance_service.services.ap_calculations import (
    ApCalculationError,
    calculate_payable_outstanding,
    calculate_payables_aging,
    calculate_supplier_invoice_totals,
)


def build_supplier_invoice() -> SupplierInvoiceCreate:
    return SupplierInvoiceCreate(
        tenant_id=uuid4(),
        vendor_id=uuid4(),
        fiscal_period_id=uuid4(),
        invoice_number="SUP-INV-001",
        invoice_date=date(2026, 1, 1),
        due_date=date(2026, 1, 31),
        created_by=uuid4(),
        lines=[
            SupplierInvoiceLineCreate(
                line_number=1,
                description="Animal feed purchase",
                quantity=Decimal("10"),
                unit_price=Decimal("100"),
                discount_amount=Decimal("100"),
                tax_rate=Decimal("10"),
                withholding_tax_rate=Decimal("5"),
                expense_account_id=uuid4(),
            )
        ],
    )


def test_supplier_invoice_totals() -> None:
    values = calculate_supplier_invoice_totals(
        build_supplier_invoice()
    )

    assert values == (
        Decimal("1000.00"),
        Decimal("100.00"),
        Decimal("90.00"),
        Decimal("45.00"),
        Decimal("945.00"),
    )


def test_payable_outstanding() -> None:
    assert calculate_payable_outstanding(
        total_amount=Decimal("1000"),
        paid_amount=Decimal("300"),
        debited_amount=Decimal("100"),
    ) == Decimal("600.00")


def test_payable_overallocation_rejected() -> None:
    with pytest.raises(ApCalculationError):
        calculate_payable_outstanding(
            total_amount=Decimal("100"),
            paid_amount=Decimal("90"),
            debited_amount=Decimal("20"),
        )


def test_payables_aging() -> None:
    tenant_id = uuid4()
    vendor_id = uuid4()

    aging = calculate_payables_aging(
        tenant_id=tenant_id,
        vendor_id=vendor_id,
        as_of_date=date(2026, 5, 1),
        due_date=date(2026, 1, 1),
        outstanding_amount=Decimal("500"),
    )

    assert aging.over_90 == Decimal("500.00")
    assert aging.total == Decimal("500.00")

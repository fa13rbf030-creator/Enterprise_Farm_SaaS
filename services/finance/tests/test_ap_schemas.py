from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.core.enums import PaymentMethod
from finance_service.schemas.ap import (
    SupplierInvoiceCreate,
    SupplierInvoiceLineCreate,
    VendorPaymentCreate,
)


def test_supplier_invoice_due_date_validation() -> None:
    with pytest.raises(ValidationError):
        SupplierInvoiceCreate(
            tenant_id=uuid4(),
            vendor_id=uuid4(),
            fiscal_period_id=uuid4(),
            invoice_number="SUP-1",
            invoice_date=date(2026, 2, 1),
            due_date=date(2026, 1, 1),
            created_by=uuid4(),
            lines=[
                SupplierInvoiceLineCreate(
                    line_number=1,
                    description="Purchase",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100"),
                    expense_account_id=uuid4(),
                )
            ],
        )


def test_vendor_payment_schema() -> None:
    payment = VendorPaymentCreate(
        tenant_id=uuid4(),
        vendor_id=uuid4(),
        fiscal_period_id=uuid4(),
        payment_number="PAY-1",
        payment_date=date(2026, 1, 1),
        amount=Decimal("100"),
        payment_method=PaymentMethod.BANK_TRANSFER,
        cash_account_id=uuid4(),
        created_by=uuid4(),
    )

    assert payment.amount == Decimal("100")

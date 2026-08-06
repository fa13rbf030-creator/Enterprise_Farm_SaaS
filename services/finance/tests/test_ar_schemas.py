from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.schemas.ar import (
    InvoiceCreate,
    InvoiceLineCreate,
    ReceiptCreate,
)
from finance_service.core.enums import PaymentMethod


def test_invoice_due_date_validation() -> None:
    with pytest.raises(ValidationError):
        InvoiceCreate(
            tenant_id=uuid4(),
            customer_id=uuid4(),
            fiscal_period_id=uuid4(),
            invoice_number="INV-1",
            invoice_date=date(2026, 2, 1),
            due_date=date(2026, 1, 1),
            created_by=uuid4(),
            lines=[
                InvoiceLineCreate(
                    line_number=1,
                    description="Sale",
                    quantity=Decimal("1"),
                    unit_price=Decimal("100"),
                    revenue_account_id=uuid4(),
                )
            ],
        )


def test_receipt_schema() -> None:
    receipt = ReceiptCreate(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        fiscal_period_id=uuid4(),
        receipt_number="RCPT-1",
        receipt_date=date(2026, 1, 1),
        amount=Decimal("100"),
        payment_method=PaymentMethod.CASH,
        created_by=uuid4(),
    )

    assert receipt.amount == Decimal("100")

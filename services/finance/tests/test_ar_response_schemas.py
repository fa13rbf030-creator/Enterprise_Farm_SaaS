from datetime import date
from decimal import Decimal
from uuid import uuid4

from finance_service.schemas.ar import (
    CustomerAgingRead,
    ReceiptPostRequest,
)


def test_receipt_post_request() -> None:
    payload = ReceiptPostRequest(
        tenant_id=uuid4(),
        cash_account_id=uuid4(),
        posted_by=uuid4(),
    )

    assert payload.cash_account_id is not None


def test_customer_aging_read() -> None:
    aging = CustomerAgingRead(
        tenant_id=uuid4(),
        customer_id=None,
        as_of_date=date(2026, 8, 6),
        current=Decimal("10"),
        days_1_30=Decimal("20"),
        days_31_60=Decimal("30"),
        days_61_90=Decimal("40"),
        over_90=Decimal("50"),
        total=Decimal("150"),
    )

    assert aging.total == Decimal("150")

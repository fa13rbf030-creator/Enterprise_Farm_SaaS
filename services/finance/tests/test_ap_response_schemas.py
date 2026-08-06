from datetime import date
from decimal import Decimal
from uuid import uuid4

from finance_service.schemas.ap import PayablesAgingRead


def test_payables_aging_read() -> None:
    aging = PayablesAgingRead(
        tenant_id=uuid4(),
        vendor_id=None,
        as_of_date=date(2026, 8, 6),
        current=Decimal("10"),
        days_1_30=Decimal("20"),
        days_31_60=Decimal("30"),
        days_61_90=Decimal("40"),
        over_90=Decimal("50"),
        total=Decimal("150"),
    )

    assert aging.total == Decimal("150")

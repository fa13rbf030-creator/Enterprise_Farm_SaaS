from decimal import Decimal
from uuid import uuid4

from finance_service.schemas.closing import (
    FiscalYearClosePreview,
)


def test_fiscal_year_close_preview() -> None:
    preview = FiscalYearClosePreview(
        tenant_id=uuid4(),
        fiscal_year_id=uuid4(),
        revenue_total=Decimal("100"),
        expense_total=Decimal("40"),
        net_income=Decimal("60"),
        lines=[],
    )

    assert preview.net_income == Decimal("60")

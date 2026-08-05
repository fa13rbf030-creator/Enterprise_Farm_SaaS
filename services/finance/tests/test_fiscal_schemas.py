from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.schemas.gl import (
    FiscalPeriodCreate,
    FiscalYearCreate,
)


def test_valid_fiscal_year() -> None:
    fiscal_year = FiscalYearCreate(
        tenant_id=uuid4(),
        name="FY 2026",
        starts_on=date(2026, 1, 1),
        ends_on=date(2026, 12, 31),
    )

    assert fiscal_year.name == "FY 2026"


def test_invalid_fiscal_year_dates_are_rejected() -> None:
    with pytest.raises(ValidationError):
        FiscalYearCreate(
            tenant_id=uuid4(),
            name="Invalid FY",
            starts_on=date(2026, 12, 31),
            ends_on=date(2026, 1, 1),
        )


def test_invalid_period_dates_are_rejected() -> None:
    with pytest.raises(ValidationError):
        FiscalPeriodCreate(
            tenant_id=uuid4(),
            fiscal_year_id=uuid4(),
            period_number=1,
            name="January",
            starts_on=date(2026, 1, 31),
            ends_on=date(2026, 1, 1),
        )

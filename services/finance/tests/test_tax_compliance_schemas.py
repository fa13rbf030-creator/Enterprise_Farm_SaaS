from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.schemas.tax_compliance import (
    TaxPeriodCreate,
    TaxRegistrationCreate,
)


def test_registration_rejects_invalid_dates():
    with pytest.raises(ValidationError):
        TaxRegistrationCreate(
            tenant_id=uuid4(),
            jurisdiction_id=uuid4(),
            registration_number="REG-1",
            legal_name="Enterprise Farm",
            effective_from=date(2026, 8, 7),
            effective_to=date(2026, 8, 6),
        )


def test_tax_period_rejects_invalid_range():
    with pytest.raises(ValidationError):
        TaxPeriodCreate(
            tenant_id=uuid4(),
            registration_id=uuid4(),
            period_name="August",
            period_start=date(2026, 8, 31),
            period_end=date(2026, 8, 1),
            filing_due_date=date(2026, 9, 15),
        )

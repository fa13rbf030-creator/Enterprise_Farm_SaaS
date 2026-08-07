from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.schemas.islamic_finance import (
    LivestockZakatRuleCreate,
    ShariahRuleSetCreate,
)


def test_rule_set_rejects_invalid_dates():
    with pytest.raises(ValidationError):
        ShariahRuleSetCreate(
            tenant_id=uuid4(),
            rule_code="ZAKAT",
            rule_name="Zakat Policy",
            effective_from=date(2026, 8, 7),
            effective_to=date(2026, 8, 6),
        )


def test_livestock_rule_rejects_invalid_range():
    with pytest.raises(ValidationError):
        LivestockZakatRuleCreate(
            tenant_id=uuid4(),
            rule_set_id=uuid4(),
            species_code="CATTLE",
            minimum_count=40,
            maximum_count=30,
            obligation_quantity=1,
            obligation_unit="animal",
        )

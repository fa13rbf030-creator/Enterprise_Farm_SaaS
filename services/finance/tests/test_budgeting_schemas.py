from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.core.enums import (
    BudgetType,
    CostObjectType,
)
from finance_service.schemas.budgeting import (
    BudgetCreate,
    BudgetLineCreate,
)


def build_line(line_number: int) -> BudgetLineCreate:
    return BudgetLineCreate(
        line_number=line_number,
        ledger_account_id=uuid4(),
        fiscal_period_id=uuid4(),
        object_type=CostObjectType.FARM,
        quantity=Decimal("10"),
        unit_rate=Decimal("100"),
    )


def test_budget_rejects_invalid_dates() -> None:
    with pytest.raises(ValidationError):
        BudgetCreate(
            tenant_id=uuid4(),
            budget_number="BUD-1",
            name="Annual Budget",
            budget_type=BudgetType.ANNUAL,
            fiscal_year_id=uuid4(),
            starts_on=date(2027, 12, 31),
            ends_on=date(2027, 1, 1),
            created_by=uuid4(),
            lines=[build_line(1)],
        )


def test_budget_rejects_duplicate_lines() -> None:
    with pytest.raises(ValidationError):
        BudgetCreate(
            tenant_id=uuid4(),
            budget_number="BUD-2",
            name="Annual Budget",
            budget_type=BudgetType.ANNUAL,
            fiscal_year_id=uuid4(),
            starts_on=date(2027, 1, 1),
            ends_on=date(2027, 12, 31),
            created_by=uuid4(),
            lines=[
                build_line(1),
                build_line(1),
            ],
        )

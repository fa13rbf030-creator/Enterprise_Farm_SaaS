from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.core.enums import (
    FinancialCloseCycleType,
    FinancialCloseTaskType,
)
from finance_service.schemas.financial_close import (
    FinancialCloseCycleCreate,
    FinancialCloseTaskCreate,
)


def test_close_cycle_rejects_invalid_period() -> None:
    with pytest.raises(ValidationError):
        FinancialCloseCycleCreate(
            tenant_id=uuid4(),
            cycle_code="CLOSE-1",
            cycle_name="August Close",
            cycle_type=FinancialCloseCycleType.MONTH_END,
            period_start=date(2026, 8, 31),
            period_end=date(2026, 8, 1),
            opened_by=uuid4(),
        )


def test_close_cycle_rejects_duplicate_task_codes() -> None:
    task = FinancialCloseTaskCreate(
        task_code="TB",
        task_name="Trial Balance",
        task_type=FinancialCloseTaskType.TRIAL_BALANCE_VALIDATION,
        owner_id=uuid4(),
    )

    with pytest.raises(ValidationError):
        FinancialCloseCycleCreate(
            tenant_id=uuid4(),
            cycle_code="CLOSE-2",
            cycle_name="August Close",
            cycle_type=FinancialCloseCycleType.MONTH_END,
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 31),
            opened_by=uuid4(),
            tasks=[task, task],
        )

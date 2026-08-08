from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from finance_service.models.finance_controls import (
    FinanceControlFrequency,
    FinanceControlType,
)
from finance_service.schemas.finance_controls import (
    FinanceControlDefinitionCreate,
    FinanceControlExecutionCreate,
)


def test_control_rejects_invalid_dates():
    with pytest.raises(ValidationError):
        FinanceControlDefinitionCreate(
            tenant_id=uuid4(),
            control_code="CTRL-1",
            control_name="Control",
            control_type=FinanceControlType.PREVENTIVE,
            frequency=FinanceControlFrequency.MONTHLY,
            owner_id=uuid4(),
            module_name="GL",
            effective_from=date(2026, 8, 7),
            effective_to=date(2026, 8, 6),
        )


def test_execution_rejects_excess_check_counts():
    with pytest.raises(ValidationError):
        FinanceControlExecutionCreate(
            tenant_id=uuid4(),
            control_id=uuid4(),
            execution_number="EXEC-1",
            execution_date=date(2026, 8, 7),
            tested_population=10,
            passed_checks=8,
            failed_checks=3,
            executed_by=uuid4(),
        )

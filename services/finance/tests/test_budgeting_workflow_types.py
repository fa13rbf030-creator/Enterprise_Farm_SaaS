import pytest

from finance_service.services.budgeting import (
    BudgetWorkflowError,
)


def test_budget_workflow_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise BudgetWorkflowError(
            "budget workflow failed"
        )

import pytest

from finance_service.services.opening_balance_workflow import (
    OpeningBalanceWorkflowError,
)


def test_opening_balance_workflow_error() -> None:
    with pytest.raises(ValueError):
        raise OpeningBalanceWorkflowError(
            "invalid opening balance"
        )

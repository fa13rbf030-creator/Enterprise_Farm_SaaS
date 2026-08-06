import pytest

from finance_service.services.banking import (
    BankingWorkflowError,
)


def test_banking_workflow_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise BankingWorkflowError(
            "banking workflow failed"
        )

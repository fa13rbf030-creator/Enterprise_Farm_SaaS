import pytest

from finance_service.services.finance_controls import (
    FinanceControlWorkflowError,
)


def test_finance_control_error_is_value_error():
    with pytest.raises(ValueError):
        raise FinanceControlWorkflowError(
            "finance control workflow failed"
        )

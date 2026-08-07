import pytest

from finance_service.services.islamic_finance import (
    IslamicFinanceWorkflowError,
)


def test_islamic_finance_error_is_value_error():
    with pytest.raises(ValueError):
        raise IslamicFinanceWorkflowError(
            "islamic finance workflow failed"
        )

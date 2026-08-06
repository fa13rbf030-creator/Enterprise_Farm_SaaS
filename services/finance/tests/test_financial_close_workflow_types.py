import pytest

from finance_service.services.financial_close import (
    FinancialCloseWorkflowError,
)


def test_financial_close_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise FinancialCloseWorkflowError(
            "financial close workflow failed"
        )

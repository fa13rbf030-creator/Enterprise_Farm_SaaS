import pytest

from finance_service.services.finance_analytics import (
    FinanceAnalyticsWorkflowError,
)


def test_finance_analytics_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise FinanceAnalyticsWorkflowError(
            "analytics workflow failed"
        )

import pytest

from finance_service.services.financial_reporting import (
    FinancialReportingWorkflowError,
)


def test_financial_reporting_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise FinancialReportingWorkflowError(
            "financial reporting workflow failed"
        )

import pytest

from finance_service.services.treasury import (
    TreasuryWorkflowError,
)


def test_treasury_workflow_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise TreasuryWorkflowError(
            "treasury workflow failed"
        )

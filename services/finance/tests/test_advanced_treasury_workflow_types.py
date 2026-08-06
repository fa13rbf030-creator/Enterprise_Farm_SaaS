import pytest

from finance_service.services.advanced_treasury import (
    AdvancedTreasuryWorkflowError,
)


def test_advanced_treasury_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise AdvancedTreasuryWorkflowError(
            "advanced treasury failure"
        )

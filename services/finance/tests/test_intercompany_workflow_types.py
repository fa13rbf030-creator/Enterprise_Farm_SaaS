import pytest

from finance_service.services.intercompany import (
    IntercompanyWorkflowError,
)


def test_intercompany_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise IntercompanyWorkflowError(
            "intercompany workflow failed"
        )

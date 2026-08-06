import pytest

from finance_service.services.ar import ArWorkflowError


def test_ar_workflow_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise ArWorkflowError("AR workflow failed")

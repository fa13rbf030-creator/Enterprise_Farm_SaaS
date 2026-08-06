import pytest

from finance_service.services.ap import ApWorkflowError


def test_ap_workflow_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise ApWorkflowError("AP workflow failed")

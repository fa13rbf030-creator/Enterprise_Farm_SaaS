import pytest

from finance_service.services.tax_compliance import (
    TaxComplianceWorkflowError,
)


def test_tax_compliance_error_is_value_error():
    with pytest.raises(ValueError):
        raise TaxComplianceWorkflowError(
            "tax compliance workflow failed"
        )

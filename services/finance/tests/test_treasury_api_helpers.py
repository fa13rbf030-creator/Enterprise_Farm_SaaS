from finance_service.api.treasury import (
    translate_treasury_error,
)
from finance_service.services.treasury import (
    TreasuryWorkflowError,
)


def test_treasury_error_translation() -> None:
    error = translate_treasury_error(
        TreasuryWorkflowError(
            "invalid treasury operation"
        )
    )

    assert error.status_code == 422
    assert error.detail == "invalid treasury operation"

from finance_service.api.banking import (
    translate_banking_error,
)
from finance_service.services.banking import (
    BankingWorkflowError,
)


def test_banking_error_translation() -> None:
    error = translate_banking_error(
        BankingWorkflowError(
            "invalid banking transaction"
        )
    )

    assert error.status_code == 422
    assert error.detail == (
        "invalid banking transaction"
    )

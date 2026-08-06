from finance_service.api.ar import translate_ar_error
from finance_service.services.ar import ArWorkflowError


def test_ar_error_translation() -> None:
    error = translate_ar_error(
        ArWorkflowError("invalid AR transaction")
    )

    assert error.status_code == 422
    assert error.detail == "invalid AR transaction"

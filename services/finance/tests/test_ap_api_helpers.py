from finance_service.api.ap import translate_ap_error
from finance_service.services.ap import ApWorkflowError


def test_ap_error_translation() -> None:
    error = translate_ap_error(
        ApWorkflowError("invalid AP transaction")
    )

    assert error.status_code == 422
    assert error.detail == "invalid AP transaction"

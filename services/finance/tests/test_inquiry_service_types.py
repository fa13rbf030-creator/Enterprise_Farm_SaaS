from datetime import date

import pytest

from finance_service.services.inquiry import (
    InquiryValidationError,
)


def test_inquiry_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise InquiryValidationError(
            "invalid inquiry"
        )


def test_date_order_validation_message() -> None:
    date_from = date(2026, 2, 1)
    date_to = date(2026, 1, 1)

    assert date_to < date_from

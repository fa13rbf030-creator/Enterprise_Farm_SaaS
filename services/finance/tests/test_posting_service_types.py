import pytest

from finance_service.services.posting import (
    PostingValidationError,
)


def test_posting_validation_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise PostingValidationError(
            "posting failed"
        )

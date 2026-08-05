import pytest

from finance_service.services.gl import (
    DuplicateFinanceRecordError,
    GlValidationError,
)


def test_gl_validation_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise GlValidationError("invalid GL record")


def test_duplicate_record_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise DuplicateFinanceRecordError(
            "duplicate record"
        )

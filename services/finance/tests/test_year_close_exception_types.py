from finance_service.services.gl import (
    DuplicateFinanceRecordError,
    GlValidationError,
)
from finance_service.services.posting import (
    PostingValidationError,
)
from finance_service.services.year_close import (
    FiscalYearCloseWorkflowError,
)


def test_year_close_domain_errors_are_value_errors() -> None:
    errors = (
        GlValidationError("gl validation"),
        DuplicateFinanceRecordError("duplicate record"),
        PostingValidationError("posting validation"),
        FiscalYearCloseWorkflowError("year close"),
    )

    assert all(
        isinstance(error, ValueError)
        for error in errors
    )


def test_expected_year_close_dependency_error_types() -> None:
    dependency_errors = (
        GlValidationError,
        DuplicateFinanceRecordError,
        PostingValidationError,
    )

    assert len(dependency_errors) == 3
    assert len(set(dependency_errors)) == 3

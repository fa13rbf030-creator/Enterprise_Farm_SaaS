from uuid import uuid4

import pytest

from identity_service.services.security import (
    PasswordResetIssue,
    SecurityValidationError,
)


def test_password_reset_issue_hides_account_state() -> None:
    issue = PasswordResetIssue(
        accepted=True,
        raw_token=None,
    )

    assert issue.accepted is True
    assert issue.raw_token is None


def test_security_validation_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise SecurityValidationError(
            "invalid token"
        )


def test_password_reset_issue_can_hold_development_token() -> None:
    issue = PasswordResetIssue(
        accepted=True,
        raw_token=str(uuid4()),
    )

    assert issue.raw_token is not None

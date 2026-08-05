import pytest

from identity_service.services.mfa import (
    MfaValidationError,
)
from identity_service.services.sessions import (
    SessionValidationError,
)


def test_mfa_validation_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise MfaValidationError("invalid mfa")


def test_session_validation_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise SessionValidationError("invalid session")

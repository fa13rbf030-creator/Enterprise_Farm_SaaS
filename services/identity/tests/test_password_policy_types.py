import pytest

from identity_service.services.password_policy import (
    PasswordReuseError,
)


def test_password_reuse_error_is_value_error() -> None:
    with pytest.raises(ValueError):
        raise PasswordReuseError(
            "password reused"
        )

from uuid import uuid4

import pytest
from pydantic import ValidationError

from identity_service.schemas.security import (
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
)


def test_password_reset_request_schema() -> None:
    payload = PasswordResetRequest(
        tenant_id=uuid4(),
        email="user@example.com",
    )

    assert payload.email == "user@example.com"


def test_password_reset_requires_strong_password() -> None:
    with pytest.raises(ValidationError):
        PasswordResetConfirm(
            tenant_id=uuid4(),
            token="x" * 32,
            new_password="short",
        )


def test_logout_requires_refresh_token() -> None:
    with pytest.raises(ValidationError):
        LogoutRequest(refresh_token="tiny")

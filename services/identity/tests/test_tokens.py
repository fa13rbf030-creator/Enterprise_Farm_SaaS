from uuid import uuid4

import pytest

from identity_service.core.tokens import (
    TokenType,
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_access_token_contains_tenant_and_permissions() -> None:
    user_id = uuid4()
    tenant_id = uuid4()

    token = create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
        permissions=[
            "identity.users.read",
            "identity.users.write",
            "identity.users.read",
        ],
    )

    payload = decode_token(
        token,
        expected_type=TokenType.ACCESS,
    )

    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["permissions"] == [
        "identity.users.read",
        "identity.users.write",
    ]


def test_refresh_token_has_correct_type() -> None:
    token = create_refresh_token(
        subject=uuid4(),
        tenant_id=uuid4(),
    )

    payload = decode_token(
        token,
        expected_type=TokenType.REFRESH,
    )

    assert payload["type"] == "refresh"


def test_access_token_cannot_be_used_as_refresh_token() -> None:
    token = create_access_token(
        subject=uuid4(),
        tenant_id=uuid4(),
    )

    with pytest.raises(
        TokenValidationError,
        match="Unexpected token type",
    ):
        decode_token(
            token,
            expected_type=TokenType.REFRESH,
        )


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(
        subject=uuid4(),
        tenant_id=uuid4(),
    )

    tampered = token[:-1] + (
        "a" if token[-1] != "a" else "b"
    )

    with pytest.raises(
        TokenValidationError,
        match="Invalid or expired token",
    ):
        decode_token(
            tampered,
            expected_type=TokenType.ACCESS,
        )

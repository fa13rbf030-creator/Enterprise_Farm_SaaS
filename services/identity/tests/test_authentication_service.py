from uuid import uuid4

from identity_service.core.tokens import (
    TokenType,
    decode_token,
)
from identity_service.repositories.users import normalize_email
from identity_service.services.authentication import (
    build_token_response,
)


def test_email_normalization() -> None:
    assert normalize_email(
        "  ADMIN@Example.COM "
    ) == "admin@example.com"


def test_token_response_contains_valid_token_pair() -> None:
    user_id = uuid4()
    tenant_id = uuid4()

    response = build_token_response(
        user_id=user_id,
        tenant_id=tenant_id,
        permissions=["identity.users.read"],
    )

    access_payload = decode_token(
        response.access_token,
        expected_type=TokenType.ACCESS,
    )
    refresh_payload = decode_token(
        response.refresh_token,
        expected_type=TokenType.REFRESH,
    )

    assert access_payload["sub"] == str(user_id)
    assert access_payload["tenant_id"] == str(tenant_id)
    assert access_payload["permissions"] == [
        "identity.users.read"
    ]

    assert refresh_payload["sub"] == str(user_id)
    assert refresh_payload["tenant_id"] == str(tenant_id)
    assert response.token_type == "bearer"
    assert response.expires_in > 0

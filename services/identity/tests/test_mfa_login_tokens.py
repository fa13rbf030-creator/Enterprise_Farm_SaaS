from uuid import uuid4

from identity_service.core.tokens import (
    TokenType,
    create_mfa_challenge_token,
    decode_token,
)
from identity_service.services.mfa_login import (
    create_mfa_login_challenge,
)


def test_mfa_challenge_token_type() -> None:
    user_id = uuid4()
    tenant_id = uuid4()

    token = create_mfa_challenge_token(
        subject=user_id,
        tenant_id=tenant_id,
    )

    payload = decode_token(
        token,
        expected_type=TokenType.MFA_CHALLENGE,
    )

    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)


def test_mfa_challenge_response() -> None:
    response = create_mfa_login_challenge(
        tenant_id=uuid4(),
        user_id=uuid4(),
    )

    assert response.mfa_required is True
    assert len(response.challenge_token) > 20

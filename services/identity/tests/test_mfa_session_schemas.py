from datetime import UTC, datetime, timedelta
from uuid import uuid4

from identity_service.schemas.mfa import (
    MfaEnrollmentResponse,
    MfaLoginChallenge,
)
from identity_service.schemas.session import (
    SessionRead,
)


def test_mfa_enrollment_response() -> None:
    payload = MfaEnrollmentResponse(
        secret="SECRET",
        provisioning_uri="otpauth://totp/test",
    )

    assert payload.secret == "SECRET"


def test_mfa_login_challenge_defaults_required() -> None:
    payload = MfaLoginChallenge(
        challenge_token="x" * 32,
    )

    assert payload.mfa_required is True


def test_session_schema_supports_revocation_state() -> None:
    now = datetime.now(UTC)

    payload = SessionRead(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        ip_address="127.0.0.1",
        user_agent="pytest",
        device_name="Test Device",
        is_trusted=False,
        last_seen_at=now,
        expires_at=now + timedelta(days=1),
        revoked_at=None,
        created_at=now,
    )

    assert payload.revoked_at is None

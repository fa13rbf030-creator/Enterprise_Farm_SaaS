from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.core.tokens import (
    TokenType,
    TokenValidationError,
    create_mfa_challenge_token,
    decode_token,
)
from identity_service.repositories.mfa import (
    is_mfa_enabled,
)
from identity_service.repositories.users import (
    get_user_by_id,
    get_user_permissions,
)
from identity_service.schemas.mfa import (
    MfaLoginChallenge,
)
from identity_service.services.mfa import (
    verify_mfa_or_recovery_code,
)


class MfaLoginError(ValueError):
    pass


async def user_requires_mfa(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> bool:
    return await is_mfa_enabled(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )


def create_mfa_login_challenge(
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> MfaLoginChallenge:
    return MfaLoginChallenge(
        challenge_token=create_mfa_challenge_token(
            subject=user_id,
            tenant_id=tenant_id,
        )
    )


async def verify_mfa_login_challenge(
    session: AsyncSession,
    *,
    challenge_token: str,
    code: str,
):
    try:
        payload = decode_token(
            challenge_token,
            expected_type=TokenType.MFA_CHALLENGE,
        )
    except TokenValidationError as exc:
        raise MfaLoginError(
            "Invalid or expired MFA challenge"
        ) from exc

    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])

    user = await get_user_by_id(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    if user is None or not user.is_active:
        raise MfaLoginError(
            "Invalid or expired MFA challenge"
        )

    valid = await verify_mfa_or_recovery_code(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        code=code,
    )

    if not valid:
        raise MfaLoginError("Invalid MFA code")

    permissions = await get_user_permissions(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    if user.is_superuser:
        permissions = sorted(
            set([*permissions, "*"])
        )

    return user, permissions

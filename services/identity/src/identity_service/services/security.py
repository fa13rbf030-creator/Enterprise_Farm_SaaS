from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.core.config import get_settings
from identity_service.core.opaque_tokens import (
    generate_opaque_token,
    hash_opaque_token,
)
from identity_service.core.security import hash_password
from identity_service.core.tokens import (
    TokenType,
    TokenValidationError,
    decode_token,
)
from identity_service.models.security import PasswordResetToken
from identity_service.repositories.security import (
    get_valid_password_reset_token,
    invalidate_active_password_reset_tokens,
    is_token_revoked,
    revoke_token,
)
from identity_service.repositories.users import (
    get_user_by_email,
    get_user_by_id,
)


class SecurityValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PasswordResetIssue:
    accepted: bool
    raw_token: str | None = None


async def issue_password_reset(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    email: str,
) -> PasswordResetIssue:
    user = await get_user_by_email(
        session,
        tenant_id=tenant_id,
        email=email,
    )

    if user is None or not user.is_active:
        return PasswordResetIssue(accepted=True)

    await invalidate_active_password_reset_tokens(
        session,
        tenant_id=tenant_id,
        user_id=user.id,
    )

    raw_token = generate_opaque_token()
    settings = get_settings()

    token = PasswordResetToken(
        tenant_id=tenant_id,
        user_id=user.id,
        token_hash=hash_opaque_token(raw_token),
        expires_at=datetime.now(UTC)
        + timedelta(minutes=settings.password_reset_minutes),
    )

    session.add(token)
    await session.commit()

    return PasswordResetIssue(
        accepted=True,
        raw_token=raw_token,
    )


async def confirm_password_reset(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    raw_token: str,
    new_password: str,
) -> UUID:
    token = await get_valid_password_reset_token(
        session,
        tenant_id=tenant_id,
        token_hash=hash_opaque_token(raw_token),
    )

    if token is None:
        raise SecurityValidationError(
            "Invalid or expired password reset token"
        )

    user = await get_user_by_id(
        session,
        tenant_id=tenant_id,
        user_id=token.user_id,
    )

    if user is None or not user.is_active:
        raise SecurityValidationError(
            "Invalid or expired password reset token"
        )

    now = datetime.now(UTC)

    from identity_service.services.password_policy import (
        PasswordReuseError,
        replace_user_password,
    )

    try:
        await replace_user_password(
            session,
            user=user,
            new_password=new_password,
        )
    except PasswordReuseError as exc:
        raise SecurityValidationError(
            str(exc)
        ) from exc

    user.password_changed_at = now
    user.failed_login_attempts = 0
    user.locked_until = None
    token.used_at = now

    await session.commit()

    return user.id


async def revoke_refresh_token(
    session: AsyncSession,
    *,
    refresh_token: str,
    reason: str = "logout",
) -> UUID:
    try:
        payload = decode_token(
            refresh_token,
            expected_type=TokenType.REFRESH,
        )
    except TokenValidationError as exc:
        raise SecurityValidationError(
            "Invalid refresh token"
        ) from exc

    token_id = UUID(payload["jti"])
    tenant_id = UUID(payload["tenant_id"])
    user_id = UUID(payload["sub"])
    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=UTC,
    )

    await revoke_token(
        session,
        token_id=token_id,
        tenant_id=tenant_id,
        user_id=user_id,
        token_type=TokenType.REFRESH.value,
        expires_at=expires_at,
        reason=reason,
    )

    await session.commit()
    return token_id


async def ensure_refresh_token_active(
    session: AsyncSession,
    *,
    refresh_token: str,
) -> dict:
    try:
        payload = decode_token(
            refresh_token,
            expected_type=TokenType.REFRESH,
        )
    except TokenValidationError as exc:
        raise SecurityValidationError(
            "Invalid refresh token"
        ) from exc

    token_id = UUID(payload["jti"])

    if await is_token_revoked(
        session,
        token_id=token_id,
    ):
        raise SecurityValidationError(
            "Refresh token has been revoked"
        )

    return payload

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.models.security import (
    PasswordResetToken,
    RevokedToken,
)


async def get_valid_password_reset_token(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    token_hash: str,
) -> PasswordResetToken | None:
    result = await session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.tenant_id == tenant_id,
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(UTC),
        )
    )

    return result.scalar_one_or_none()


async def invalidate_active_password_reset_tokens(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> None:
    await session.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.tenant_id == tenant_id,
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )


async def is_token_revoked(
    session: AsyncSession,
    *,
    token_id: UUID,
) -> bool:
    result = await session.execute(
        select(RevokedToken.id).where(
            RevokedToken.token_id == token_id
        )
    )

    return result.scalar_one_or_none() is not None


async def revoke_token(
    session: AsyncSession,
    *,
    token_id: UUID,
    tenant_id: UUID,
    user_id: UUID,
    token_type: str,
    expires_at: datetime,
    reason: str,
) -> RevokedToken:
    existing = await session.execute(
        select(RevokedToken).where(
            RevokedToken.token_id == token_id
        )
    )

    revoked = existing.scalar_one_or_none()

    if revoked is not None:
        return revoked

    revoked = RevokedToken(
        token_id=token_id,
        tenant_id=tenant_id,
        user_id=user_id,
        token_type=token_type,
        reason=reason,
        expires_at=expires_at,
    )

    session.add(revoked)
    await session.flush()

    return revoked

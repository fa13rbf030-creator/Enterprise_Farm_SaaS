from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.repositories.security import revoke_token
from identity_service.repositories.sessions import (
    get_user_session,
    revoke_all_user_sessions,
    revoke_user_session,
)


class SessionValidationError(ValueError):
    pass


async def revoke_session_and_token(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    session_id: UUID,
    reason: str = "session_revoked",
) -> None:
    record = await revoke_user_session(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    if record is None:
        raise SessionValidationError("Session not found")

    await revoke_token(
        session,
        token_id=record.refresh_token_id,
        tenant_id=tenant_id,
        user_id=user_id,
        token_type="refresh",
        expires_at=record.expires_at,
        reason=reason,
    )

    await session.commit()


async def revoke_all_sessions_and_tokens(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> int:
    records = await revoke_all_user_sessions(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    for record in records:
        await revoke_token(
            session,
            token_id=record.refresh_token_id,
            tenant_id=tenant_id,
            user_id=user_id,
            token_type="refresh",
            expires_at=record.expires_at,
            reason="revoke_all_sessions",
        )

    await session.commit()
    return len(records)


async def update_session_trust(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    session_id: UUID,
    is_trusted: bool,
):
    record = await get_user_session(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    if record is None:
        raise SessionValidationError("Session not found")

    record.is_trusted = is_trusted
    await session.commit()
    await session.refresh(record)
    return record

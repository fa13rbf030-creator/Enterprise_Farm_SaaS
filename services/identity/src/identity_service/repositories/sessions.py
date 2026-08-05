from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.models.session import (
    PasswordHistory,
    UserSession,
)


async def create_user_session(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    refresh_token_id: UUID,
    expires_at: datetime,
    ip_address: str | None,
    user_agent: str | None,
    device_name: str | None = None,
) -> UserSession:
    record = UserSession(
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_id=refresh_token_id,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
        device_name=device_name,
    )

    session.add(record)
    await session.flush()
    return record


async def list_active_sessions(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> list[UserSession]:
    result = await session.execute(
        select(UserSession)
        .where(
            UserSession.tenant_id == tenant_id,
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(UTC),
        )
        .order_by(UserSession.created_at.desc())
    )

    return list(result.scalars().all())


async def get_user_session(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    session_id: UUID,
) -> UserSession | None:
    result = await session.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.tenant_id == tenant_id,
            UserSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def revoke_user_session(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    session_id: UUID,
) -> UserSession | None:
    record = await get_user_session(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
    )

    if record is None:
        return None

    if record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)

    await session.flush()
    return record


async def revoke_all_user_sessions(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> list[UserSession]:
    records = await list_active_sessions(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    now = datetime.now(UTC)

    for record in records:
        record.revoked_at = now

    await session.flush()
    return records


async def list_password_history(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    limit: int,
) -> list[PasswordHistory]:
    result = await session.execute(
        select(PasswordHistory)
        .where(
            PasswordHistory.tenant_id == tenant_id,
            PasswordHistory.user_id == user_id,
        )
        .order_by(PasswordHistory.created_at.desc())
        .limit(limit)
    )

    return list(result.scalars().all())


async def add_password_history(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    password_hash: str,
) -> PasswordHistory:
    record = PasswordHistory(
        tenant_id=tenant_id,
        user_id=user_id,
        password_hash=password_hash,
    )

    session.add(record)
    await session.flush()
    return record

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.models.mfa import (
    MfaRecoveryCode,
    UserMfaSetting,
)


async def get_mfa_setting(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> UserMfaSetting | None:
    result = await session.execute(
        select(UserMfaSetting).where(
            UserMfaSetting.tenant_id == tenant_id,
            UserMfaSetting.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def replace_recovery_codes(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    code_hashes: list[str],
) -> None:
    await session.execute(
        delete(MfaRecoveryCode).where(
            MfaRecoveryCode.tenant_id == tenant_id,
            MfaRecoveryCode.user_id == user_id,
        )
    )

    for code_hash in code_hashes:
        session.add(
            MfaRecoveryCode(
                tenant_id=tenant_id,
                user_id=user_id,
                code_hash=code_hash,
            )
        )


async def consume_recovery_code(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    code_hash: str,
) -> bool:
    result = await session.execute(
        select(MfaRecoveryCode).where(
            MfaRecoveryCode.tenant_id == tenant_id,
            MfaRecoveryCode.user_id == user_id,
            MfaRecoveryCode.code_hash == code_hash,
            MfaRecoveryCode.used_at.is_(None),
        )
    )

    recovery = result.scalar_one_or_none()

    if recovery is None:
        return False

    recovery.used_at = datetime.now(UTC)
    await session.flush()
    return True


async def is_mfa_enabled(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> bool:
    setting = await get_mfa_setting(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    return bool(
        setting is not None
        and setting.is_enabled
    )

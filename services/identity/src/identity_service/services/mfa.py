from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.core.mfa import (
    build_totp_uri,
    generate_recovery_codes,
    generate_totp_secret,
    hash_recovery_code,
    verify_totp_code,
)
from identity_service.models.mfa import UserMfaSetting
from identity_service.repositories.mfa import (
    consume_recovery_code,
    get_mfa_setting,
    replace_recovery_codes,
)


class MfaValidationError(ValueError):
    pass


async def begin_mfa_enrollment(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    account_name: str,
) -> tuple[UserMfaSetting, str]:
    setting = await get_mfa_setting(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    secret = generate_totp_secret()

    if setting is None:
        setting = UserMfaSetting(
            tenant_id=tenant_id,
            user_id=user_id,
            secret=secret,
            is_enabled=False,
        )
        session.add(setting)
    else:
        setting.secret = secret
        setting.is_enabled = False
        setting.verified_at = None

    await session.commit()
    await session.refresh(setting)

    uri = build_totp_uri(
        secret=secret,
        account_name=account_name,
    )

    return setting, uri


async def verify_and_enable_mfa(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    code: str,
) -> list[str]:
    setting = await get_mfa_setting(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    if setting is None:
        raise MfaValidationError("MFA enrollment not found")

    if not verify_totp_code(
        secret=setting.secret,
        code=code,
    ):
        raise MfaValidationError("Invalid MFA code")

    setting.is_enabled = True
    setting.verified_at = datetime.now(UTC)

    recovery_codes = generate_recovery_codes()

    await replace_recovery_codes(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        code_hashes=[
            hash_recovery_code(code)
            for code in recovery_codes
        ],
    )

    await session.commit()
    return recovery_codes


async def verify_mfa_or_recovery_code(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    code: str,
) -> bool:
    setting = await get_mfa_setting(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    if setting is None or not setting.is_enabled:
        return False

    if verify_totp_code(
        secret=setting.secret,
        code=code,
    ):
        return True

    consumed = await consume_recovery_code(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        code_hash=hash_recovery_code(code),
    )

    if consumed:
        await session.commit()

    return consumed


async def disable_mfa(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    code: str,
) -> None:
    valid = await verify_mfa_or_recovery_code(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        code=code,
    )

    if not valid:
        raise MfaValidationError("Invalid MFA code")

    setting = await get_mfa_setting(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    if setting is None:
        raise MfaValidationError("MFA setting not found")

    setting.is_enabled = False
    setting.verified_at = None

    await replace_recovery_codes(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        code_hashes=[],
    )

    await session.commit()

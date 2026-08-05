from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.core.config import get_settings
from identity_service.core.security import (
    hash_password,
    verify_password,
)
from identity_service.models.user import User
from identity_service.repositories.sessions import (
    add_password_history,
    list_password_history,
)


class PasswordReuseError(ValueError):
    pass


async def ensure_password_not_reused(
    session: AsyncSession,
    *,
    user: User,
    new_password: str,
) -> None:
    settings = get_settings()

    if verify_password(
        new_password,
        user.password_hash,
    ):
        raise PasswordReuseError(
            "New password cannot match the current password"
        )

    history = await list_password_history(
        session,
        tenant_id=user.tenant_id,
        user_id=user.id,
        limit=settings.password_history_count,
    )

    for record in history:
        if verify_password(
            new_password,
            record.password_hash,
        ):
            raise PasswordReuseError(
                "Password was recently used"
            )


async def replace_user_password(
    session: AsyncSession,
    *,
    user: User,
    new_password: str,
) -> None:
    await ensure_password_not_reused(
        session,
        user=user,
        new_password=new_password,
    )

    await add_password_history(
        session,
        tenant_id=user.tenant_id,
        user_id=user.id,
        password_hash=user.password_hash,
    )

    user.password_hash = hash_password(
        new_password
    )

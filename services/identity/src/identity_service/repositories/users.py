from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.models.rbac import (
    Permission,
    RolePermission,
    UserRole,
)
from identity_service.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_user_by_email(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    email: str,
) -> User | None:
    statement: Select[tuple[User]] = select(User).where(
        User.tenant_id == tenant_id,
        User.email == normalize_email(email),
    )

    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> User | None:
    statement: Select[tuple[User]] = select(User).where(
        User.id == user_id,
        User.tenant_id == tenant_id,
    )

    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_user_permissions(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
) -> list[str]:
    statement = (
        select(Permission.code)
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id,
        )
        .join(
            UserRole,
            UserRole.role_id == RolePermission.role_id,
        )
        .where(
            UserRole.user_id == user_id,
            UserRole.tenant_id == tenant_id,
        )
        .distinct()
        .order_by(Permission.code)
    )

    result = await session.execute(statement)
    return list(result.scalars().all())

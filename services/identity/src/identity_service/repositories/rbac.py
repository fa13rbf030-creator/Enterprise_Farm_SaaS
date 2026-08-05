from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.models.rbac import (
    Permission,
    Role,
    RolePermission,
    UserRole,
)


async def get_permission_by_code(
    session: AsyncSession,
    *,
    code: str,
) -> Permission | None:
    result = await session.execute(
        select(Permission).where(
            Permission.code == code.strip().lower()
        )
    )
    return result.scalar_one_or_none()


async def list_permissions(
    session: AsyncSession,
) -> list[Permission]:
    result = await session.execute(
        select(Permission).order_by(Permission.code)
    )
    return list(result.scalars().all())


async def get_role_by_id(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    role_id: UUID,
) -> Role | None:
    result = await session.execute(
        select(Role).where(
            Role.id == role_id,
            Role.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def list_roles(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> list[Role]:
    result = await session.execute(
        select(Role)
        .where(Role.tenant_id == tenant_id)
        .order_by(Role.name)
    )
    return list(result.scalars().all())


async def set_role_permissions(
    session: AsyncSession,
    *,
    role_id: UUID,
    permission_ids: list[UUID],
) -> None:
    await session.execute(
        delete(RolePermission).where(
            RolePermission.role_id == role_id
        )
    )

    for permission_id in sorted(set(permission_ids)):
        session.add(
            RolePermission(
                role_id=role_id,
                permission_id=permission_id,
            )
        )


async def set_user_roles(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    role_ids: list[UUID],
) -> None:
    await session.execute(
        delete(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.tenant_id == tenant_id,
        )
    )

    for role_id in sorted(set(role_ids)):
        session.add(
            UserRole(
                user_id=user_id,
                role_id=role_id,
                tenant_id=tenant_id,
            )
        )


async def remove_user_role(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    role_id: UUID,
) -> int:
    result = await session.execute(
        delete(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.tenant_id == tenant_id,
        )
    )
    return result.rowcount or 0

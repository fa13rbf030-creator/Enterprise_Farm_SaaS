from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.models.rbac import (
    Permission,
    Role,
)
from identity_service.models.user import User
from identity_service.repositories.rbac import (
    get_permission_by_code,
    get_role_by_id,
    set_role_permissions,
    set_user_roles,
)
from identity_service.repositories.users import get_user_by_id
from identity_service.schemas.rbac import (
    PermissionCreate,
    RoleCreate,
    UserRoleAssignment,
)


class RbacValidationError(ValueError):
    pass


class DuplicatePermissionError(ValueError):
    pass


async def create_permission(
    session: AsyncSession,
    *,
    payload: PermissionCreate,
) -> Permission:
    code = payload.code.strip().lower()

    existing = await get_permission_by_code(
        session,
        code=code,
    )

    if existing is not None:
        raise DuplicatePermissionError(
            "Permission code already exists"
        )

    permission = Permission(
        code=code,
        description=payload.description.strip(),
    )

    session.add(permission)
    await session.commit()
    await session.refresh(permission)

    return permission


async def create_role(
    session: AsyncSession,
    *,
    payload: RoleCreate,
) -> Role:
    role = Role(
        tenant_id=payload.tenant_id,
        name=payload.name.strip(),
        description=payload.description.strip(),
        is_system=False,
    )

    session.add(role)
    await session.flush()

    if payload.permission_ids:
        result = await session.execute(
            select(Permission.id).where(
                Permission.id.in_(payload.permission_ids)
            )
        )
        found_ids = set(result.scalars().all())

        if found_ids != set(payload.permission_ids):
            await session.rollback()
            raise RbacValidationError(
                "One or more permissions do not exist"
            )

        await set_role_permissions(
            session,
            role_id=role.id,
            permission_ids=payload.permission_ids,
        )

    await session.commit()
    await session.refresh(role)

    return role


async def assign_roles_to_user(
    session: AsyncSession,
    *,
    payload: UserRoleAssignment,
) -> User:
    user = await get_user_by_id(
        session,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
    )

    if user is None:
        raise RbacValidationError("User not found in tenant")

    result = await session.execute(
        select(Role).where(
            Role.id.in_(payload.role_ids)
        )
    )
    roles = list(result.scalars().all())

    if len(roles) != len(set(payload.role_ids)):
        raise RbacValidationError(
            "One or more roles do not exist"
        )

    if any(
        role.tenant_id != payload.tenant_id
        for role in roles
    ):
        raise RbacValidationError(
            "Cross-tenant role assignment is not allowed"
        )

    await set_user_roles(
        session,
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
        role_ids=payload.role_ids,
    )

    await session.commit()
    return user


async def validate_role_for_tenant(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    role_id: UUID,
) -> Role:
    role = await get_role_by_id(
        session,
        tenant_id=tenant_id,
        role_id=role_id,
    )

    if role is None:
        raise RbacValidationError("Role not found in tenant")

    return role

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.api.dependencies import (
    CurrentIdentity,
    enforce_tenant_header,
    require_permission,
)
from identity_service.api.request_context import (
    get_client_ip,
    get_user_agent,
)
from identity_service.db.session import get_db_session
from identity_service.repositories.audit import record_audit_event
from identity_service.repositories.rbac import (
    list_permissions,
    list_roles,
    remove_user_role,
    set_role_permissions,
)
from identity_service.schemas.rbac import (
    PermissionCreate,
    PermissionRead,
    RoleCreate,
    RolePermissionAssignment,
    RoleRead,
    UserRoleAssignment,
)
from identity_service.schemas.user import UserRead
from identity_service.services.rbac import (
    DuplicatePermissionError,
    RbacValidationError,
    assign_roles_to_user,
    create_permission,
    create_role,
    validate_role_for_tenant,
)


router = APIRouter(
    prefix="/rbac",
    tags=["rbac"],
)


@router.get(
    "/permissions",
    response_model=list[PermissionRead],
)
async def get_permissions(
    identity: CurrentIdentity = Depends(
        require_permission("identity.permissions.read")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    del identity
    return await list_permissions(session)


@router.post(
    "/permissions",
    response_model=PermissionRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_permission(
    payload: PermissionCreate,
    request: Request,
    identity: CurrentIdentity = Depends(
        require_permission("identity.permissions.write")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        permission = await create_permission(
            session,
            payload=payload,
        )
    except DuplicatePermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        session,
        tenant_id=identity.tenant_id,
        actor_id=identity.user.id,
        event_type="identity.permission.create",
        outcome="success",
        resource_type="permission",
        resource_id=str(permission.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"code": permission.code},
    )

    return permission


@router.get(
    "/roles",
    response_model=list[RoleRead],
)
async def get_roles(
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("identity.roles.read")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    del identity
    return await list_roles(
        session,
        tenant_id=tenant_id,
    )


@router.post(
    "/roles",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_role(
    payload: RoleCreate,
    request: Request,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("identity.roles.write")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    if payload.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )

    try:
        role = await create_role(
            session,
            payload=payload,
        )
    except RbacValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        session,
        tenant_id=tenant_id,
        actor_id=identity.user.id,
        event_type="identity.role.create",
        outcome="success",
        resource_type="role",
        resource_id=str(role.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"name": role.name},
    )

    return role


@router.put(
    "/roles/{role_id}/permissions",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def replace_role_permissions(
    role_id: UUID,
    payload: RolePermissionAssignment,
    request: Request,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("identity.roles.write")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    if payload.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )

    try:
        role = await validate_role_for_tenant(
            session,
            tenant_id=tenant_id,
            role_id=role_id,
        )
    except RbacValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if role.is_system and not identity.has_ceo_override:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System role is protected",
        )

    await set_role_permissions(
        session,
        role_id=role.id,
        permission_ids=payload.permission_ids,
    )
    await session.commit()

    await record_audit_event(
        session,
        tenant_id=tenant_id,
        actor_id=identity.user.id,
        event_type="identity.role.permissions.replace",
        outcome="success",
        resource_type="role",
        resource_id=str(role.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "permission_count": len(
                set(payload.permission_ids)
            ),
            "ceo_override": identity.has_ceo_override,
        },
    )


@router.put(
    "/users/{user_id}/roles",
    response_model=UserRead,
)
async def replace_user_roles(
    user_id: UUID,
    payload: UserRoleAssignment,
    request: Request,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("identity.user_roles.write")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    if (
        payload.tenant_id != tenant_id
        or payload.user_id != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant or user mismatch",
        )

    try:
        user = await assign_roles_to_user(
            session,
            payload=payload,
        )
    except RbacValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        session,
        tenant_id=tenant_id,
        actor_id=identity.user.id,
        event_type="identity.user_roles.replace",
        outcome="success",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "role_count": len(set(payload.role_ids)),
            "ceo_override": identity.has_ceo_override,
        },
    )

    return user


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_role(
    user_id: UUID,
    role_id: UUID,
    request: Request,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("identity.user_roles.write")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    deleted = await remove_user_role(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        role_id=role_id,
    )

    await session.commit()

    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role assignment not found",
        )

    await record_audit_event(
        session,
        tenant_id=tenant_id,
        actor_id=identity.user.id,
        event_type="identity.user_role.remove",
        outcome="success",
        resource_type="user",
        resource_id=str(user_id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "role_id": str(role_id),
            "ceo_override": identity.has_ceo_override,
        },
    )

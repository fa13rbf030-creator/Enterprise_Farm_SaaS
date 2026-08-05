from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
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
from identity_service.repositories.users import (
    get_user_by_id,
    list_users,
)
from identity_service.schemas.user import UserRead


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "",
    response_model=list[UserRead],
)
async def get_users(
    request: Request,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("identity.users.read")
    ),
    session: AsyncSession = Depends(get_db_session),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list:
    users = await list_users(
        session,
        tenant_id=tenant_id,
        offset=offset,
        limit=limit,
    )

    await record_audit_event(
        session,
        tenant_id=tenant_id,
        actor_id=identity.user.id,
        event_type="identity.users.list",
        outcome="success",
        resource_type="user",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "offset": offset,
            "limit": limit,
            "result_count": len(users),
            "ceo_override": identity.has_ceo_override,
        },
    )

    return users


@router.get(
    "/{user_id}",
    response_model=UserRead,
)
async def get_user(
    user_id: UUID,
    request: Request,
    tenant_id: UUID = Depends(enforce_tenant_header),
    identity: CurrentIdentity = Depends(
        require_permission("identity.users.read")
    ),
    session: AsyncSession = Depends(get_db_session),
):
    user = await get_user_by_id(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    if user is None:
        await record_audit_event(
            session,
            tenant_id=tenant_id,
            actor_id=identity.user.id,
            event_type="identity.users.read",
            outcome="not_found",
            resource_type="user",
            resource_id=str(user_id),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await record_audit_event(
        session,
        tenant_id=tenant_id,
        actor_id=identity.user.id,
        event_type="identity.users.read",
        outcome="success",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={
            "ceo_override": identity.has_ceo_override,
        },
    )

    return user

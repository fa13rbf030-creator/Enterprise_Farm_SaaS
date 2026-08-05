from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.api.dependencies import (
    CurrentIdentity,
    get_current_identity,
)
from identity_service.db.session import get_db_session
from identity_service.repositories.sessions import (
    list_active_sessions,
)
from identity_service.schemas.session import (
    RevokeAllSessionsResponse,
    SessionRead,
    SessionTrustUpdate,
)
from identity_service.services.sessions import (
    SessionValidationError,
    revoke_all_sessions_and_tokens,
    revoke_session_and_token,
    update_session_trust,
)


router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
)


@router.get(
    "",
    response_model=list[SessionRead],
)
async def get_sessions(
    identity: CurrentIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_active_sessions(
        session,
        tenant_id=identity.tenant_id,
        user_id=identity.user.id,
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_session(
    session_id: UUID,
    identity: CurrentIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    try:
        await revoke_session_and_token(
            session,
            tenant_id=identity.tenant_id,
            user_id=identity.user.id,
            session_id=session_id,
        )
    except SessionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "",
    response_model=RevokeAllSessionsResponse,
)
async def delete_all_sessions(
    identity: CurrentIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_db_session),
) -> RevokeAllSessionsResponse:
    count = await revoke_all_sessions_and_tokens(
        session,
        tenant_id=identity.tenant_id,
        user_id=identity.user.id,
    )

    return RevokeAllSessionsResponse(
        revoked_count=count,
    )


@router.patch(
    "/{session_id}/trust",
    response_model=SessionRead,
)
async def patch_session_trust(
    session_id: UUID,
    payload: SessionTrustUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await update_session_trust(
            session,
            tenant_id=identity.tenant_id,
            user_id=identity.user.id,
            session_id=session_id,
            is_trusted=payload.is_trusted,
        )
    except SessionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

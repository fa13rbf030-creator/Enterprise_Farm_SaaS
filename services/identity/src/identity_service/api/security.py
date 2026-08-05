from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.api.request_context import (
    get_client_ip,
    get_user_agent,
)
from identity_service.db.session import get_db_session
from identity_service.repositories.audit import record_audit_event
from identity_service.schemas.security import (
    LogoutRequest,
    LogoutResponse,
    PasswordResetAccepted,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from identity_service.services.security import (
    SecurityValidationError,
    confirm_password_reset,
    issue_password_reset,
    revoke_refresh_token,
)


router = APIRouter(
    prefix="/security",
    tags=["security"],
)


@router.post(
    "/password-reset/request",
    response_model=PasswordResetAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> PasswordResetAccepted:
    issue = await issue_password_reset(
        session,
        tenant_id=payload.tenant_id,
        email=payload.email,
    )

    details = {
        "email": str(payload.email).lower(),
    }

    if issue.raw_token is not None:
        details["development_reset_token"] = issue.raw_token

    await record_audit_event(
        session,
        tenant_id=payload.tenant_id,
        event_type="identity.password_reset.request",
        outcome="accepted",
        resource_type="user",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details=details,
    )

    return PasswordResetAccepted()


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def confirm_reset(
    payload: PasswordResetConfirm,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    try:
        user_id = await confirm_password_reset(
            session,
            tenant_id=payload.tenant_id,
            raw_token=payload.token,
            new_password=payload.new_password,
        )
    except SecurityValidationError as exc:
        await record_audit_event(
            session,
            tenant_id=payload.tenant_id,
            event_type="identity.password_reset.confirm",
            outcome="denied",
            resource_type="user",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"reason": "invalid_or_expired_token"},
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        session,
        tenant_id=payload.tenant_id,
        actor_id=user_id,
        event_type="identity.password_reset.confirm",
        outcome="success",
        resource_type="user",
        resource_id=str(user_id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    payload: LogoutRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> LogoutResponse:
    try:
        token_id = await revoke_refresh_token(
            session,
            refresh_token=payload.refresh_token,
        )
    except SecurityValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        session,
        event_type="identity.authentication.logout",
        outcome="success",
        resource_type="token",
        resource_id=str(token_id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    return LogoutResponse()

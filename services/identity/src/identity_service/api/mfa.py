from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.api.dependencies import CurrentIdentity
from identity_service.api.dependencies import get_current_identity
from identity_service.api.request_context import (
    get_client_ip,
    get_user_agent,
)
from identity_service.db.session import get_db_session
from identity_service.repositories.audit import record_audit_event
from identity_service.schemas.auth import TokenResponse
from identity_service.schemas.mfa import (
    MfaDisableRequest,
    MfaEnrollmentResponse,
    MfaRecoveryResponse,
    MfaVerificationRequest,
)
from identity_service.services.mfa import (
    MfaValidationError,
    begin_mfa_enrollment,
    disable_mfa,
    verify_and_enable_mfa,
)


router = APIRouter(
    prefix="/mfa",
    tags=["mfa"],
)


@router.post(
    "/enroll",
    response_model=MfaEnrollmentResponse,
)
async def enroll_mfa(
    request: Request,
    identity: CurrentIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_db_session),
) -> MfaEnrollmentResponse:
    setting, uri = await begin_mfa_enrollment(
        session,
        tenant_id=identity.tenant_id,
        user_id=identity.user.id,
        account_name=identity.user.email,
    )

    await record_audit_event(
        session,
        tenant_id=identity.tenant_id,
        actor_id=identity.user.id,
        event_type="identity.mfa.enrollment_started",
        outcome="success",
        resource_type="user",
        resource_id=str(identity.user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    return MfaEnrollmentResponse(
        secret=setting.secret,
        provisioning_uri=uri,
    )


@router.post(
    "/verify",
    response_model=MfaRecoveryResponse,
)
async def verify_mfa(
    payload: MfaVerificationRequest,
    request: Request,
    identity: CurrentIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_db_session),
) -> MfaRecoveryResponse:
    try:
        codes = await verify_and_enable_mfa(
            session,
            tenant_id=identity.tenant_id,
            user_id=identity.user.id,
            code=payload.code,
        )
    except MfaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        session,
        tenant_id=identity.tenant_id,
        actor_id=identity.user.id,
        event_type="identity.mfa.enabled",
        outcome="success",
        resource_type="user",
        resource_id=str(identity.user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    return MfaRecoveryResponse(
        recovery_codes=codes,
    )


@router.post(
    "/disable",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def disable_mfa_endpoint(
    payload: MfaDisableRequest,
    request: Request,
    identity: CurrentIdentity = Depends(get_current_identity),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    try:
        await disable_mfa(
            session,
            tenant_id=identity.tenant_id,
            user_id=identity.user.id,
            code=payload.code,
        )
    except MfaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        session,
        tenant_id=identity.tenant_id,
        actor_id=identity.user.id,
        event_type="identity.mfa.disabled",
        outcome="success",
        resource_type="user",
        resource_id=str(identity.user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@router.post(
    "/login/verify",
    response_model=TokenResponse,
)
async def verify_mfa_login(
    payload: MfaLoginVerifyRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    from identity_service.api.request_context import (
        get_client_ip,
        get_user_agent,
    )
    from identity_service.core.config import get_settings
    from identity_service.schemas.auth import TokenResponse
    from identity_service.schemas.mfa import (
        MfaLoginVerifyRequest,
    )
    from identity_service.services.mfa_login import (
        MfaLoginError,
        verify_mfa_login_challenge,
    )
    from identity_service.services.token_sessions import (
        issue_token_pair_with_session,
    )

    try:
        user, permissions = (
            await verify_mfa_login_challenge(
                session,
                challenge_token=payload.challenge_token,
                code=payload.code,
            )
        )
    except MfaLoginError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    settings = get_settings()

    response = await issue_token_pair_with_session(
        session,
        user_id=user.id,
        tenant_id=user.tenant_id,
        permissions=permissions,
        expires_in=(
            settings.access_token_minutes * 60
        ),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    await record_audit_event(
        session,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        event_type="identity.mfa.login_verified",
        outcome="success",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    return response

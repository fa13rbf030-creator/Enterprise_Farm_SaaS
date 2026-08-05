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

from identity_service.api.dependencies import get_current_user
from identity_service.api.request_context import (
    get_client_ip,
    get_user_agent,
)
from identity_service.db.session import get_db_session
from identity_service.models.user import User
from identity_service.repositories.audit import record_audit_event
from identity_service.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from identity_service.schemas.mfa import MfaLoginChallenge
from identity_service.schemas.user import UserCreate, UserRead
from identity_service.services.authentication import (
    AuthenticationError,
    DuplicateUserError,
    authenticate_user,
    build_token_response,
    refresh_identity_tokens,
    register_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        user = await register_user(
            session,
            payload=payload,
        )
    except DuplicateUserError as exc:
        await record_audit_event(
            session,
            tenant_id=payload.tenant_id,
            event_type="identity.user.registration",
            outcome="denied",
            resource_type="user",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "email": str(payload.email).lower(),
                "reason": "duplicate_user",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    await record_audit_event(
        session,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        event_type="identity.user.registration",
        outcome="success",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        details={"email": user.email},
    )

    return user


@router.post(
    "/login",
    response_model=TokenResponse | MfaLoginChallenge,
)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    try:
        identity = await authenticate_user(
            session,
            tenant_id=payload.tenant_id,
            email=payload.email,
            password=payload.password,
        )
    except AuthenticationError as exc:
        await record_audit_event(
            session,
            tenant_id=payload.tenant_id,
            event_type="identity.authentication.login",
            outcome="denied",
            resource_type="user",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "email": str(payload.email).lower(),
                "reason": "invalid_credentials",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    await record_audit_event(
        session,
        tenant_id=identity.user.tenant_id,
        actor_id=identity.user.id,
        event_type="identity.authentication.login",
        outcome="success",
        resource_type="user",
        resource_id=str(identity.user.id),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    from identity_service.core.config import get_settings
    from identity_service.services.mfa_login import (
        create_mfa_login_challenge,
        user_requires_mfa,
    )
    from identity_service.services.token_sessions import (
        issue_token_pair_with_session,
    )

    if await user_requires_mfa(
        session,
        tenant_id=identity.user.tenant_id,
        user_id=identity.user.id,
    ):
        return create_mfa_login_challenge(
            tenant_id=identity.user.tenant_id,
            user_id=identity.user.id,
        )

    settings = get_settings()

    return await issue_token_pair_with_session(
        session,
        user_id=identity.user.id,
        tenant_id=identity.user.tenant_id,
        permissions=identity.permissions,
        expires_in=settings.access_token_minutes * 60,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    payload: RefreshTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    try:
        token_response = await refresh_identity_tokens(
            session,
            refresh_token=payload.refresh_token,
        )
    except AuthenticationError as exc:
        await record_audit_event(
            session,
            event_type="identity.authentication.refresh",
            outcome="denied",
            resource_type="token",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={"reason": "invalid_refresh_token"},
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    await record_audit_event(
        session,
        event_type="identity.authentication.refresh",
        outcome="success",
        resource_type="token",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    return token_response


@router.get(
    "/me",
    response_model=UserRead,
)
async def me(
    user: User = Depends(get_current_user),
) -> User:
    return user

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.api.dependencies import get_current_user
from identity_service.db.session import get_db_session
from identity_service.models.user import User
from identity_service.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
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
    session: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        return await register_user(
            session,
            payload=payload,
        )
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    payload: LoginRequest,
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return build_token_response(
        user_id=identity.user.id,
        tenant_id=identity.user.tenant_id,
        permissions=identity.permissions,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    try:
        return await refresh_identity_tokens(
            session,
            refresh_token=payload.refresh_token,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get(
    "/me",
    response_model=UserRead,
)
async def me(
    user: User = Depends(get_current_user),
) -> User:
    return user

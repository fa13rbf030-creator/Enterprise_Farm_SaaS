from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.core.config import get_settings
from identity_service.core.security import (
    hash_password,
    verify_password,
)
from identity_service.core.tokens import (
    TokenType,
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from identity_service.models.user import User
from identity_service.repositories.users import (
    get_user_by_email,
    get_user_by_id,
    get_user_permissions,
    normalize_email,
)
from identity_service.schemas.auth import TokenResponse
from identity_service.schemas.user import UserCreate


class AuthenticationError(ValueError):
    pass


class DuplicateUserError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    user: User
    permissions: list[str]


def build_token_response(
    *,
    user_id: UUID,
    tenant_id: UUID,
    permissions: list[str],
) -> TokenResponse:
    settings = get_settings()

    return TokenResponse(
        access_token=create_access_token(
            subject=user_id,
            tenant_id=tenant_id,
            permissions=permissions,
        ),
        refresh_token=create_refresh_token(
            subject=user_id,
            tenant_id=tenant_id,
        ),
        expires_in=settings.access_token_minutes * 60,
    )


async def register_user(
    session: AsyncSession,
    *,
    payload: UserCreate,
) -> User:
    existing = await get_user_by_email(
        session,
        tenant_id=payload.tenant_id,
        email=payload.email,
    )

    if existing is not None:
        raise DuplicateUserError(
            "A user with this email already exists in the tenant"
        )

    user = User(
        tenant_id=payload.tenant_id,
        email=normalize_email(payload.email),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
    )

    session.add(user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateUserError(
            "A user with this email already exists in the tenant"
        ) from exc

    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    email: str,
    password: str,
) -> AuthenticatedIdentity:
    user = await get_user_by_email(
        session,
        tenant_id=tenant_id,
        email=email,
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(password, user.password_hash)
    ):
        raise AuthenticationError("Invalid credentials")

    permissions = await get_user_permissions(
        session,
        tenant_id=tenant_id,
        user_id=user.id,
    )

    if user.is_superuser:
        permissions = sorted(set([*permissions, "*"]))

    return AuthenticatedIdentity(
        user=user,
        permissions=permissions,
    )


async def refresh_identity_tokens(
    session: AsyncSession,
    *,
    refresh_token: str,
) -> TokenResponse:
    try:
        payload = decode_token(
            refresh_token,
            expected_type=TokenType.REFRESH,
        )
    except TokenValidationError as exc:
        raise AuthenticationError("Invalid refresh token") from exc

    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])

    user = await get_user_by_id(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    if user is None or not user.is_active:
        raise AuthenticationError("Invalid refresh token")

    permissions = await get_user_permissions(
        session,
        tenant_id=tenant_id,
        user_id=user.id,
    )

    if user.is_superuser:
        permissions = sorted(set([*permissions, "*"]))

    return build_token_response(
        user_id=user.id,
        tenant_id=user.tenant_id,
        permissions=permissions,
    )

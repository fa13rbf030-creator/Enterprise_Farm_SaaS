from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import (
    Depends,
    Header,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from identity_service.core.permissions import has_permission
from identity_service.core.tokens import (
    TokenType,
    TokenValidationError,
    decode_token,
)
from identity_service.db.session import get_db_session
from identity_service.models.user import User
from identity_service.repositories.security import (
    is_token_revoked,
)
from identity_service.repositories.users import get_user_by_id


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


@dataclass(frozen=True, slots=True)
class CurrentIdentity:
    user: User
    permissions: frozenset[str]
    token_id: UUID
    tenant_id: UUID

    @property
    def has_ceo_override(self) -> bool:
        return self.user.is_superuser or "*" in self.permissions


async def get_current_identity(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> CurrentIdentity:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(
            token,
            expected_type=TokenType.ACCESS,
        )

        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])
        token_id = UUID(payload["jti"])
    except (
        KeyError,
        TypeError,
        ValueError,
        TokenValidationError,
    ) as exc:
        raise credentials_error from exc

    if await is_token_revoked(
        session,
        token_id=token_id,
    ):
        raise credentials_error

    user = await get_user_by_id(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    if user is None or not user.is_active:
        raise credentials_error

    permissions = frozenset(
        str(permission).strip().lower()
        for permission in payload.get("permissions", [])
        if str(permission).strip()
    )

    if user.is_superuser:
        permissions = frozenset({*permissions, "*"})

    return CurrentIdentity(
        user=user,
        permissions=permissions,
        token_id=token_id,
        tenant_id=tenant_id,
    )


async def get_current_user(
    identity: CurrentIdentity = Depends(get_current_identity),
) -> User:
    return identity.user


async def enforce_tenant_header(
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    identity: CurrentIdentity = Depends(get_current_identity),
) -> UUID:
    if identity.has_ceo_override:
        return x_tenant_id

    if x_tenant_id != identity.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )

    return x_tenant_id


def require_permission(
    permission: str,
) -> Callable:
    async def dependency(
        identity: CurrentIdentity = Depends(
            get_current_identity
        ),
    ) -> CurrentIdentity:
        if identity.has_ceo_override:
            return identity

        if not has_permission(
            identity.permissions,
            permission,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )

        return identity

    return dependency

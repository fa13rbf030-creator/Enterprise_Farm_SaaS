from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import (
    Depends,
    Header,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer

from farm_shared.security import (
    SecurityPrincipal,
    TokenValidationError,
    has_permission,
    principal_from_access_token,
)
from procurement_service.core.config import (
    Settings,
    get_settings,
)


CurrentIdentity = SecurityPrincipal


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


async def get_current_identity(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> CurrentIdentity:
    try:
        return principal_from_access_token(
            token,
            secret=settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
            issuer=settings.token_issuer,
        )
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc


async def enforce_tenant_header(
    x_tenant_id: UUID = Header(
        ...,
        alias="X-Tenant-ID",
    ),
    identity: CurrentIdentity = Depends(
        get_current_identity
    ),
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
                detail=(
                    "Missing permission: "
                    f"{permission}"
                ),
            )

        return identity

    return dependency

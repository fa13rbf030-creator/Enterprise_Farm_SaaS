from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException

from farm_shared.security import SecurityPrincipal
from procurement_service.api.security import (
    enforce_tenant_header,
    get_current_identity,
    require_permission,
)
from procurement_service.core.config import get_settings


def build_access_token(
    *,
    user_id=None,
    tenant_id=None,
    permissions=None,
):
    settings = get_settings()

    user_id = user_id or uuid4()
    tenant_id = tenant_id or uuid4()

    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "access",
        "iss": settings.token_issuer,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=5),
        "jti": str(uuid4()),
        "permissions": permissions or [],
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return token, user_id, tenant_id


@pytest.mark.asyncio
async def test_get_current_identity_accepts_valid_access_token():
    token, user_id, tenant_id = build_access_token(
        permissions=[
            "procurement.approvals.read",
        ]
    )

    identity = await get_current_identity(
        token=token,
        settings=get_settings(),
    )

    assert identity.user_id == user_id
    assert identity.tenant_id == tenant_id
    assert (
        "procurement.approvals.read"
        in identity.permissions
    )


@pytest.mark.asyncio
async def test_get_current_identity_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_identity(
            token="not-a-valid-jwt",
            settings=get_settings(),
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_tenant_header_accepts_matching_tenant():
    tenant_id = uuid4()

    identity = SecurityPrincipal(
        user_id=uuid4(),
        tenant_id=tenant_id,
        token_id=uuid4(),
        permissions=frozenset(),
    )

    result = await enforce_tenant_header(
        x_tenant_id=tenant_id,
        identity=identity,
    )

    assert result == tenant_id


@pytest.mark.asyncio
async def test_tenant_header_rejects_foreign_tenant():
    identity = SecurityPrincipal(
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_id=uuid4(),
        permissions=frozenset(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await enforce_tenant_header(
            x_tenant_id=uuid4(),
            identity=identity,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Tenant access denied"


@pytest.mark.asyncio
async def test_ceo_override_allows_cross_tenant_header():
    requested_tenant = uuid4()

    identity = SecurityPrincipal(
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_id=uuid4(),
        permissions=frozenset({"*"}),
    )

    result = await enforce_tenant_header(
        x_tenant_id=requested_tenant,
        identity=identity,
    )

    assert result == requested_tenant


@pytest.mark.asyncio
async def test_exact_permission_dependency_accepts_identity():
    identity = SecurityPrincipal(
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_id=uuid4(),
        permissions=frozenset(
            {"procurement.approvals.read"}
        ),
    )

    dependency = require_permission(
        "procurement.approvals.read"
    )

    result = await dependency(identity=identity)

    assert result is identity


@pytest.mark.asyncio
async def test_hierarchical_permission_dependency_accepts_identity():
    identity = SecurityPrincipal(
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_id=uuid4(),
        permissions=frozenset(
            {"procurement.approvals.*"}
        ),
    )

    dependency = require_permission(
        "procurement.approvals.approve"
    )

    result = await dependency(identity=identity)

    assert result is identity


@pytest.mark.asyncio
async def test_permission_dependency_rejects_missing_permission():
    identity = SecurityPrincipal(
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_id=uuid4(),
        permissions=frozenset(
            {"procurement.approvals.read"}
        ),
    )

    dependency = require_permission(
        "procurement.approvals.approve"
    )

    with pytest.raises(HTTPException) as exc_info:
        await dependency(identity=identity)

    assert exc_info.value.status_code == 403
    assert (
        exc_info.value.detail
        == (
            "Missing permission: "
            "procurement.approvals.approve"
        )
    )


@pytest.mark.asyncio
async def test_global_override_satisfies_any_permission():
    identity = SecurityPrincipal(
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_id=uuid4(),
        permissions=frozenset({"*"}),
    )

    dependency = require_permission(
        "procurement.approvals.cancel"
    )

    result = await dependency(identity=identity)

    assert result is identity


def test_resource_security_contract_is_stateless():
    import inspect

    import farm_shared.security as security

    source = inspect.getsource(security)

    forbidden = (
        "identity_service",
        "sqlalchemy",
        "AsyncSession",
        "get_db_session",
    )

    for value in forbidden:
        assert value not in source


def test_security_principal_keeps_token_id_for_future_revocation_contract():
    principal = SecurityPrincipal(
        user_id=uuid4(),
        tenant_id=uuid4(),
        token_id=uuid4(),
        permissions=frozenset(),
    )

    assert principal.token_id is not None

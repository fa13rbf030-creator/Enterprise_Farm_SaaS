from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from identity_service.api.dependencies import (
    CurrentIdentity,
    enforce_tenant_header,
    require_permission,
)


def make_identity(
    *,
    tenant_id=None,
    permissions=None,
    is_superuser=False,
) -> CurrentIdentity:
    tenant_id = tenant_id or uuid4()

    user = SimpleNamespace(
        is_superuser=is_superuser,
    )

    return CurrentIdentity(
        user=user,
        permissions=frozenset(permissions or []),
        token_id=uuid4(),
        tenant_id=tenant_id,
    )


@pytest.mark.asyncio
async def test_matching_tenant_is_allowed() -> None:
    tenant_id = uuid4()
    identity = make_identity(tenant_id=tenant_id)

    result = await enforce_tenant_header(
        x_tenant_id=tenant_id,
        identity=identity,
    )

    assert result == tenant_id


@pytest.mark.asyncio
async def test_cross_tenant_access_is_denied() -> None:
    identity = make_identity()

    with pytest.raises(HTTPException) as exc:
        await enforce_tenant_header(
            x_tenant_id=uuid4(),
            identity=identity,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "Tenant access denied"


@pytest.mark.asyncio
async def test_ceo_override_allows_cross_tenant_access() -> None:
    requested_tenant = uuid4()
    identity = make_identity(is_superuser=True)

    result = await enforce_tenant_header(
        x_tenant_id=requested_tenant,
        identity=identity,
    )

    assert result == requested_tenant


@pytest.mark.asyncio
async def test_permission_dependency_allows_granted_permission() -> None:
    identity = make_identity(
        permissions={"identity.users.read"},
    )
    dependency = require_permission(
        "identity.users.read"
    )

    result = await dependency(identity=identity)

    assert result is identity


@pytest.mark.asyncio
async def test_permission_dependency_denies_missing_permission() -> None:
    identity = make_identity(
        permissions={"identity.users.write"},
    )
    dependency = require_permission(
        "identity.users.read"
    )

    with pytest.raises(HTTPException) as exc:
        await dependency(identity=identity)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_global_override_bypasses_permission_check() -> None:
    identity = make_identity(
        permissions={"*"},
    )
    dependency = require_permission(
        "finance.journals.post"
    )

    result = await dependency(identity=identity)

    assert result is identity

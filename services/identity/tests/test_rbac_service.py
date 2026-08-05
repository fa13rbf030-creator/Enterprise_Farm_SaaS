from uuid import uuid4

from identity_service.schemas.rbac import (
    PermissionCreate,
    RoleCreate,
    UserRoleAssignment,
)


def test_permission_schema_normalizes_valid_code() -> None:
    payload = PermissionCreate(
        code="identity.roles.read",
        description="Read roles",
    )

    assert payload.code == "identity.roles.read"


def test_role_schema_supports_permissions() -> None:
    permission_id = uuid4()

    payload = RoleCreate(
        tenant_id=uuid4(),
        name="Identity Administrator",
        permission_ids=[permission_id],
    )

    assert payload.permission_ids == [permission_id]


def test_user_role_assignment_requires_roles() -> None:
    role_id = uuid4()

    payload = UserRoleAssignment(
        tenant_id=uuid4(),
        user_id=uuid4(),
        role_ids=[role_id],
    )

    assert payload.role_ids == [role_id]

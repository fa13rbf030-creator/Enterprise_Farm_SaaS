from identity_service.repositories.audit import record_audit_event
from identity_service.repositories.rbac import (
    get_permission_by_code,
    get_role_by_id,
    list_permissions,
    list_roles,
    remove_user_role,
    set_role_permissions,
    set_user_roles,
)
from identity_service.repositories.users import (
    get_user_by_email,
    get_user_by_id,
    get_user_permissions,
    list_users,
    normalize_email,
)

__all__ = [
    "get_user_by_email",
    "get_user_by_id",
    "get_user_permissions",
    "list_users",
    "normalize_email",
    "get_permission_by_code",
    "get_role_by_id",
    "list_permissions",
    "list_roles",
    "remove_user_role",
    "set_role_permissions",
    "set_user_roles",
    "record_audit_event",
]

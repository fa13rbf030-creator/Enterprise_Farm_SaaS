from identity_service.repositories.sessions import (
    add_password_history,
    create_user_session,
    get_user_session,
    list_active_sessions,
    list_password_history,
    revoke_all_user_sessions,
    revoke_user_session,
)
from identity_service.repositories.mfa import (
    consume_recovery_code,
    get_mfa_setting,
    replace_recovery_codes,
)
from identity_service.repositories.audit import record_audit_event
from identity_service.repositories.security import (
    get_valid_password_reset_token,
    invalidate_active_password_reset_tokens,
    is_token_revoked,
    revoke_token,
)
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
    "revoke_user_session",
    "revoke_all_user_sessions",
    "replace_recovery_codes",
    "list_password_history",
    "list_active_sessions",
    "get_user_session",
    "get_mfa_setting",
    "create_user_session",
    "consume_recovery_code",
    "add_password_history",
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
    "get_valid_password_reset_token",
    "invalidate_active_password_reset_tokens",
    "is_token_revoked",
    "revoke_token",
    "record_audit_event",
]

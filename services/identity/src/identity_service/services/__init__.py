from identity_service.services.authentication import (
    AuthenticatedIdentity,
    AuthenticationError,
    DuplicateUserError,
    authenticate_user,
    build_token_response,
    refresh_identity_tokens,
    register_user,
)

__all__ = [
    "revoke_refresh_token",
    "issue_password_reset",
    "ensure_refresh_token_active",
    "confirm_password_reset",
    "SecurityValidationError",
    "PasswordResetIssue",
    "validate_role_for_tenant",
    "create_role",
    "create_permission",
    "assign_roles_to_user",
    "RbacValidationError",
    "DuplicatePermissionError",
    "AuthenticatedIdentity",
    "AuthenticationError",
    "DuplicateUserError",
    "authenticate_user",
    "build_token_response",
    "refresh_identity_tokens",
    "register_user",
]

from identity_service.services.rbac import (
    DuplicatePermissionError,
    RbacValidationError,
    assign_roles_to_user,
    create_permission,
    create_role,
    validate_role_for_tenant,
)

from identity_service.services.security import (
    PasswordResetIssue,
    SecurityValidationError,
    confirm_password_reset,
    ensure_refresh_token_active,
    issue_password_reset,
    revoke_refresh_token,
)

from identity_service.services.mfa import (
    MfaValidationError,
    begin_mfa_enrollment,
    disable_mfa,
    verify_and_enable_mfa,
    verify_mfa_or_recovery_code,
)

from identity_service.services.sessions import (
    SessionValidationError,
    revoke_all_sessions_and_tokens,
    revoke_session_and_token,
    update_session_trust,
)

from identity_service.services.mfa_login import (
    MfaLoginError,
    create_mfa_login_challenge,
    user_requires_mfa,
    verify_mfa_login_challenge,
)

from identity_service.services.password_policy import (
    PasswordReuseError,
    ensure_password_not_reused,
    replace_user_password,
)

from identity_service.services.token_sessions import (
    issue_token_pair_with_session,
)

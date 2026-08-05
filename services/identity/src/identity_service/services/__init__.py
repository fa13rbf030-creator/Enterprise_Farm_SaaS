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

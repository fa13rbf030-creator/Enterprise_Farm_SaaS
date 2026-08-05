from __future__ import annotations


class PermissionDeniedError(PermissionError):
    pass


def normalize_permissions(
    permissions: list[str] | set[str],
) -> set[str]:
    return {
        permission.strip().lower()
        for permission in permissions
        if permission.strip()
    }


def has_permission(
    granted: list[str] | set[str],
    required: str,
) -> bool:
    granted_set = normalize_permissions(granted)
    required = required.strip().lower()

    if "*" in granted_set:
        return True

    if required in granted_set:
        return True

    parts = required.split(".")

    for index in range(len(parts) - 1, 0, -1):
        wildcard = ".".join(parts[:index]) + ".*"
        if wildcard in granted_set:
            return True

    return False


def require_permission(
    granted: list[str] | set[str],
    required: str,
) -> None:
    if not has_permission(granted, required):
        raise PermissionDeniedError(
            f"Missing required permission: {required}"
        )

import pytest

from identity_service.core.permissions import (
    PermissionDeniedError,
    has_permission,
    normalize_permissions,
    require_permission,
)


def test_permission_normalization() -> None:
    assert normalize_permissions(
        [
            " Identity.Users.Read ",
            "identity.users.read",
            "",
        ]
    ) == {"identity.users.read"}


def test_exact_permission_is_allowed() -> None:
    assert has_permission(
        {"identity.users.read"},
        "identity.users.read",
    )


def test_wildcard_permission_is_allowed() -> None:
    assert has_permission(
        {"identity.users.*"},
        "identity.users.write",
    )


def test_global_wildcard_is_allowed() -> None:
    assert has_permission(
        {"*"},
        "finance.journals.post",
    )


def test_missing_permission_is_denied() -> None:
    with pytest.raises(
        PermissionDeniedError,
        match="Missing required permission",
    ):
        require_permission(
            {"identity.users.read"},
            "identity.users.write",
        )

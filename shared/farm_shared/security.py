from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from uuid import UUID

import jwt
from jwt import InvalidTokenError


class TokenValidationError(ValueError):
    pass

# RESOURCE_SERVICE_TOKEN_POLICY
#
# Resource services validate signed short-lived access tokens locally.
# Identity remains authoritative for:
# - token issuance;
# - revocation registry;
# - user active state;
# - role/permission assignment lifecycle.
#
# This module intentionally performs no service/database lookup.
# Immediate distributed revocation requires a separate introspection,
# cache, or event-driven capability and must not be implemented here.



@dataclass(frozen=True, slots=True)
class SecurityPrincipal:
    user_id: UUID
    tenant_id: UUID
    token_id: UUID
    permissions: frozenset[str]

    @property
    def has_ceo_override(self) -> bool:
        return "*" in self.permissions


def normalize_permissions(
    permissions: Iterable[str],
) -> frozenset[str]:
    return frozenset(
        str(permission).strip().lower()
        for permission in permissions
        if str(permission).strip()
    )


def has_permission(
    granted: Iterable[str],
    required: str,
) -> bool:
    granted_set = normalize_permissions(granted)
    required = required.strip().lower()

    if not required:
        return False

    if "*" in granted_set:
        return True

    if required in granted_set:
        return True

    parts = required.split(".")

    for index in range(
        len(parts) - 1,
        0,
        -1,
    ):
        wildcard = (
            ".".join(parts[:index])
            + ".*"
        )

        if wildcard in granted_set:
            return True

    return False


def decode_access_token(
    token: str,
    *,
    secret: str,
    algorithm: str,
    issuer: str,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            issuer=issuer,
            options={
                "require": [
                    "sub",
                    "tenant_id",
                    "type",
                    "iss",
                    "iat",
                    "nbf",
                    "exp",
                    "jti",
                ],
            },
        )
    except InvalidTokenError as exc:
        raise TokenValidationError(
            "Invalid or expired token"
        ) from exc

    if payload.get("type") != "access":
        raise TokenValidationError(
            "Unexpected token type"
        )

    try:
        UUID(payload["sub"])
        UUID(payload["tenant_id"])
        UUID(payload["jti"])
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise TokenValidationError(
            "Invalid token identity claims"
        ) from exc

    return payload


def principal_from_access_token(
    token: str,
    *,
    secret: str,
    algorithm: str,
    issuer: str,
) -> SecurityPrincipal:
    payload = decode_access_token(
        token,
        secret=secret,
        algorithm=algorithm,
        issuer=issuer,
    )

    return SecurityPrincipal(
        user_id=UUID(payload["sub"]),
        tenant_id=UUID(
            payload["tenant_id"]
        ),
        token_id=UUID(payload["jti"]),
        permissions=normalize_permissions(
            payload.get(
                "permissions",
                [],
            )
        ),
    )

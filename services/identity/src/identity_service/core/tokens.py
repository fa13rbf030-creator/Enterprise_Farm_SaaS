from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError

from identity_service.core.config import get_settings


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenValidationError(ValueError):
    pass


def _create_token(
    *,
    subject: UUID,
    tenant_id: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    permissions: list[str] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "type": token_type.value,
        "iss": settings.token_issuer,
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
        "jti": str(uuid4()),
    }

    if permissions is not None:
        payload["permissions"] = sorted(set(permissions))

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(
    *,
    subject: UUID,
    tenant_id: UUID,
    permissions: list[str] | None = None,
) -> str:
    settings = get_settings()

    return _create_token(
        subject=subject,
        tenant_id=tenant_id,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_minutes),
        permissions=permissions,
    )


def create_refresh_token(
    *,
    subject: UUID,
    tenant_id: UUID,
) -> str:
    settings = get_settings()

    return _create_token(
        subject=subject,
        tenant_id=tenant_id,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_days),
    )


def decode_token(
    token: str,
    *,
    expected_type: TokenType,
) -> dict[str, Any]:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.token_issuer,
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
        raise TokenValidationError("Invalid or expired token") from exc

    if payload.get("type") != expected_type.value:
        raise TokenValidationError("Unexpected token type")

    try:
        UUID(payload["sub"])
        UUID(payload["tenant_id"])
        UUID(payload["jti"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TokenValidationError("Invalid token identity claims") from exc

    return payload

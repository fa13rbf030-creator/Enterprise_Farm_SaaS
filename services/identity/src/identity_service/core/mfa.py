from __future__ import annotations

import secrets
import string

import pyotp

from identity_service.core.config import get_settings
from identity_service.core.opaque_tokens import (
    hash_opaque_token,
)


RECOVERY_ALPHABET = (
    string.ascii_uppercase
    + string.digits
)


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_uri(
    *,
    secret: str,
    account_name: str,
) -> str:
    settings = get_settings()

    return pyotp.TOTP(secret).provisioning_uri(
        name=account_name,
        issuer_name=settings.mfa_issuer_name,
    )


def verify_totp_code(
    *,
    secret: str,
    code: str,
) -> bool:
    settings = get_settings()

    if not code or not code.isdigit():
        return False

    return bool(
        pyotp.TOTP(secret).verify(
            code,
            valid_window=settings.mfa_code_window,
        )
    )


def generate_recovery_code() -> str:
    groups = []

    for _ in range(4):
        group = "".join(
            secrets.choice(RECOVERY_ALPHABET)
            for _ in range(4)
        )
        groups.append(group)

    return "-".join(groups)


def generate_recovery_codes(
    *,
    count: int | None = None,
) -> list[str]:
    settings = get_settings()
    total = count or settings.recovery_code_count

    codes: set[str] = set()

    while len(codes) < total:
        codes.add(generate_recovery_code())

    return sorted(codes)


def hash_recovery_code(code: str) -> str:
    normalized = code.strip().upper()
    return hash_opaque_token(normalized)

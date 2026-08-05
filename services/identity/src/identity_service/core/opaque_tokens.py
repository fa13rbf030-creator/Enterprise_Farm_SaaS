from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_opaque_token(
    *,
    byte_length: int = 32,
) -> str:
    if byte_length < 16:
        raise ValueError(
            "Opaque tokens must use at least 16 random bytes"
        )

    return secrets.token_urlsafe(byte_length)


def hash_opaque_token(token: str) -> str:
    if not token:
        raise ValueError("Token cannot be empty")

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def verify_opaque_token(
    token: str,
    expected_hash: str,
) -> bool:
    if not token or not expected_hash:
        return False

    actual_hash = hash_opaque_token(token)

    return hmac.compare_digest(
        actual_hash,
        expected_hash,
    )

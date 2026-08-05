import pytest

from identity_service.core.opaque_tokens import (
    generate_opaque_token,
    hash_opaque_token,
    verify_opaque_token,
)


def test_generated_tokens_are_random() -> None:
    first = generate_opaque_token()
    second = generate_opaque_token()

    assert first != second
    assert len(first) >= 40
    assert len(second) >= 40


def test_token_hash_is_deterministic() -> None:
    token = "secure-reset-token"

    assert hash_opaque_token(token) == hash_opaque_token(token)


def test_token_verification() -> None:
    token = generate_opaque_token()
    token_hash = hash_opaque_token(token)

    assert verify_opaque_token(token, token_hash)
    assert not verify_opaque_token(
        "wrong-token",
        token_hash,
    )


def test_short_random_source_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="at least 16 random bytes",
    ):
        generate_opaque_token(byte_length=8)


def test_empty_token_hash_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Token cannot be empty",
    ):
        hash_opaque_token("")

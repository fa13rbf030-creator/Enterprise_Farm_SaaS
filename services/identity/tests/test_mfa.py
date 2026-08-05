import pyotp

from identity_service.core.mfa import (
    build_totp_uri,
    generate_recovery_codes,
    generate_totp_secret,
    hash_recovery_code,
    verify_totp_code,
)


def test_totp_secret_and_code_verification() -> None:
    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()

    assert verify_totp_code(
        secret=secret,
        code=code,
    )


def test_invalid_totp_code_is_rejected() -> None:
    secret = generate_totp_secret()

    assert not verify_totp_code(
        secret=secret,
        code="invalid",
    )


def test_totp_uri_contains_account() -> None:
    secret = generate_totp_secret()

    uri = build_totp_uri(
        secret=secret,
        account_name="admin@example.com",
    )

    assert uri.startswith("otpauth://totp/")
    assert "admin%40example.com" in uri


def test_recovery_codes_are_unique() -> None:
    codes = generate_recovery_codes(count=10)

    assert len(codes) == 10
    assert len(set(codes)) == 10
    assert all(len(code) == 19 for code in codes)


def test_recovery_code_hash_is_case_insensitive() -> None:
    assert hash_recovery_code(
        "ABCD-EFGH-IJKL-MNOP"
    ) == hash_recovery_code(
        "abcd-efgh-ijkl-mnop"
    )

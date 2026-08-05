from identity_service.core.security import hash_password, verify_password


def test_password_hashing_and_verification() -> None:
    password = "Strong-Test-Password-2026!"
    encoded = hash_password(password)

    assert encoded != password
    assert verify_password(password, encoded)
    assert not verify_password("incorrect-password", encoded)

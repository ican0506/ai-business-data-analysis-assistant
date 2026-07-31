from app.core.security import hash_password, verify_password


def test_password_is_hashed_and_can_be_verified():
    password_hash = hash_password("SecurePass123!")

    assert password_hash != "SecurePass123!"
    assert verify_password("SecurePass123!", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False

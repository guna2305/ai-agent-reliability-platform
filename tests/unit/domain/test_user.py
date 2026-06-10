from src.domain.entities import User


def test_create_user_sets_active_and_not_superuser():
    user = User.create(email="test@example.com", hashed_password="hashed", full_name="Test User")
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.email == "test@example.com"
    assert user.id is not None


def test_create_user_lowercases_email():
    user = User.create(email="  Test@EXAMPLE.COM  ", hashed_password="h", full_name="N")
    assert user.email == "test@example.com"


def test_deactivate_user():
    user = User.create(email="a@b.com", hashed_password="h", full_name="N")
    user.deactivate()
    assert user.is_active is False


def test_update_password():
    user = User.create(email="a@b.com", hashed_password="old", full_name="N")
    user.update_password("new_hash")
    assert user.hashed_password == "new_hash"

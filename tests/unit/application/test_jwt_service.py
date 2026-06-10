"""Unit tests for JWT service."""
import pytest

from src.infrastructure.security.jwt_service import (
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.infrastructure.security.password_service import hash_password, verify_password


def test_access_token_round_trip():
    token, jti = create_access_token("user-123", "test@example.com")
    payload = decode_token(token)
    assert payload.user_id == "user-123"
    assert payload.email == "test@example.com"
    assert payload.token_type == "access"
    assert payload.jti == jti


def test_refresh_token_round_trip():
    token, jti = create_refresh_token("user-456")
    payload = decode_token(token)
    assert payload.user_id == "user-456"
    assert payload.token_type == "refresh"
    assert payload.jti == jti


def test_invalid_token_raises():
    with pytest.raises(TokenInvalidError):
        decode_token("not.a.valid.jwt")


def test_tampered_token_raises():
    token, _ = create_access_token("user-1", "a@b.com")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(TokenInvalidError):
        decode_token(tampered)


def test_different_jtis_per_token():
    t1, jti1 = create_access_token("user-1", "a@b.com")
    t2, jti2 = create_access_token("user-1", "a@b.com")
    assert jti1 != jti2


def test_bcrypt_verify():
    hashed = hash_password("mypassword123")
    assert verify_password("mypassword123", hashed)
    assert not verify_password("wrongpassword", hashed)


def test_bcrypt_different_hashes_same_password():
    h1 = hash_password("secret")
    h2 = hash_password("secret")
    assert h1 != h2  # bcrypt uses random salt
    assert verify_password("secret", h1)
    assert verify_password("secret", h2)

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.infrastructure.config.settings import get_settings


class TokenPayload:
    __slots__ = ("user_id", "email", "is_superuser", "jti", "token_type", "exp")

    def __init__(
        self,
        user_id: str,
        email: str,
        is_superuser: bool,
        jti: str,
        token_type: str,
        exp: datetime,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.is_superuser = is_superuser
        self.jti = jti
        self.token_type = token_type
        self.exp = exp


def _settings():
    return get_settings()


def create_access_token(user_id: str, email: str, is_superuser: bool = False) -> tuple[str, str]:
    """Returns (encoded_token, jti)."""
    settings = _settings()
    jti = str(uuid.uuid4())
    exp = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "is_superuser": is_superuser,
        "jti": jti,
        "type": "access",
        "exp": exp,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Returns (encoded_token, jti)."""
    settings = _settings()
    jti = str(uuid.uuid4())
    exp = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "exp": exp,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti


def decode_token(token: str) -> TokenPayload:
    settings = _settings()
    try:
        data = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError(str(e))

    return TokenPayload(
        user_id=data["sub"],
        email=data.get("email", ""),
        is_superuser=data.get("is_superuser", False),
        jti=data["jti"],
        token_type=data.get("type", "access"),
        exp=datetime.fromtimestamp(data["exp"], tz=UTC),
    )


class TokenExpiredError(Exception):
    pass


class TokenInvalidError(Exception):
    def __init__(self, reason: str = "") -> None:
        self.reason = reason
        super().__init__(f"Invalid token: {reason}")

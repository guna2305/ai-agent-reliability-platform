from __future__ import annotations

from dataclasses import dataclass

from src.application.interfaces.repositories import UserRepository
from src.application.use_cases.auth.register_user import AuthTokensDTO
from src.domain.exceptions import DomainException
from src.infrastructure.cache.redis_client import get_redis
from src.infrastructure.config.settings import get_settings
from src.infrastructure.security.jwt_service import create_access_token, create_refresh_token
from src.infrastructure.security.password_service import verify_password


class InvalidCredentialsError(DomainException):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InactiveUserError(DomainException):
    def __init__(self) -> None:
        super().__init__("Account is deactivated")


@dataclass(frozen=True)
class LoginDTO:
    email: str
    password: str


class LoginUserUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, dto: LoginDTO) -> AuthTokensDTO:
        user = await self._user_repo.get_by_email(dto.email)
        if not user or not verify_password(dto.password, user.hashed_password):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveUserError()

        access_token, _ = create_access_token(user.id, user.email, user.is_superuser)
        refresh_token, refresh_jti = create_refresh_token(user.id)

        # Store refresh token JTI in Redis for later validation
        settings = get_settings()
        redis = get_redis()
        ttl = settings.jwt_refresh_token_expire_days * 86400
        await redis.setex(f"auth:refresh:{refresh_jti}", ttl, user.id)

        return AuthTokensDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
        )

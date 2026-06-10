"""Authentication routes: register, login, refresh, logout, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from src.application.use_cases.auth import (
    AuthTokensDTO,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    LoginDTO,
    LoginUserUseCase,
    LogoutUseCase,
    RefreshTokenDTO,
    RefreshTokenUseCase,
    RegisterUserDTO,
    RegisterUserUseCase,
)
from src.infrastructure.cache.redis_client import rate_limit_check
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.repositories import (
    PostgresOrgMemberRepository,
    PostgresOrganizationRepository,
    PostgresUserRepository,
)
from src.presentation.api.auth_dependencies import (
    CurrentUser,
    SessionDep,
    get_user_repo,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    org_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str
    user_id: str
    email: str
    full_name: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool


# ── Rate limiting helper ──────────────────────────────────────────────────────

async def _check_login_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    allowed, count = await rate_limit_check(
        key=f"rate:login:{ip}",
        max_requests=10,
        window_seconds=900,  # 10 attempts per 15 min
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in 15 minutes.",
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session: SessionDep) -> TokenResponse:
    uc = RegisterUserUseCase(
        user_repo=PostgresUserRepository(session),
        org_repo=PostgresOrganizationRepository(session),
        member_repo=PostgresOrgMemberRepository(session),
    )
    try:
        result: AuthTokensDTO = await uc.execute(
            RegisterUserDTO(
                email=body.email,
                password=body.password,
                full_name=body.full_name,
                org_name=body.org_name,
            )
        )
    except EmailAlreadyRegisteredError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        user_id=result.user_id,
        email=result.email,
        full_name=result.full_name,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    session: SessionDep,
) -> TokenResponse:
    await _check_login_rate_limit(request)

    uc = LoginUserUseCase(user_repo=PostgresUserRepository(session))
    try:
        result: AuthTokensDTO = await uc.execute(LoginDTO(email=body.email, password=body.password))
    except (InvalidCredentialsError, InactiveUserError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        user_id=result.user_id,
        email=result.email,
        full_name=result.full_name,
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(body: RefreshRequest, session: SessionDep) -> AccessTokenResponse:
    uc = RefreshTokenUseCase(user_repo=PostgresUserRepository(session))
    try:
        result: RefreshTokenDTO = await uc.execute(body.refresh_token)
    except InvalidRefreshTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)

    return AccessTokenResponse(access_token=result.access_token, token_type=result.token_type)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    current_user: CurrentUser,
    request: Request,
) -> None:
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.removeprefix("Bearer ").strip()
    uc = LogoutUseCase()
    await uc.execute(access_token=access_token, refresh_token=body.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
    )

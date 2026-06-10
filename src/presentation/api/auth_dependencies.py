"""FastAPI dependency injection for authentication and RBAC."""
from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.interfaces.repositories import (
    ApiKeyRepository,
    OrgMemberRepository,
    UserRepository,
)
from src.domain.entities import OrgMember, User
from src.infrastructure.cache.redis_client import get_redis, is_token_blacklisted
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.connection import get_db_session
from src.infrastructure.database.repositories import (
    PostgresApiKeyRepository,
    PostgresOrgMemberRepository,
    PostgresUserRepository,
)
from src.infrastructure.security.jwt_service import (
    TokenExpiredError,
    TokenInvalidError,
    decode_token,
)
from sqlalchemy.ext.asyncio import AsyncSession


# ── Session dependency ────────────────────────────────────────────────────────

async def get_session():
    async for session in get_db_session():
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ── Repository factories ──────────────────────────────────────────────────────

def get_user_repo(session: SessionDep) -> UserRepository:
    return PostgresUserRepository(session)

def get_member_repo(session: SessionDep) -> OrgMemberRepository:
    return PostgresOrgMemberRepository(session)

def get_api_key_repo(session: SessionDep) -> ApiKeyRepository:
    return PostgresApiKeyRepository(session)


# ── JWT Bearer scheme ─────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    user_repo: UserRepository = Depends(get_user_repo),
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo),
) -> User:
    """
    Supports two auth methods (checked in order):
    1. JWT Bearer token
    2. API key via 'X-API-Key' header
    """
    # 1. Try JWT
    if credentials and credentials.scheme.lower() == "bearer":
        return await _authenticate_jwt(credentials.credentials, user_repo)

    # 2. Try API key
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        return await _authenticate_api_key(api_key_header, user_repo, api_key_repo)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _authenticate_jwt(token: str, user_repo: UserRepository) -> User:
    try:
        payload = decode_token(token)
    except TokenExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except TokenInvalidError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.token_type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    if await is_token_blacklisted(payload.jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user = await user_repo.get_by_id(payload.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


async def _authenticate_api_key(
    raw_key: str,
    user_repo: UserRepository,
    api_key_repo: ApiKeyRepository,
) -> User:
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = await api_key_repo.get_by_hash(key_hash)

    if not api_key or api_key.is_expired:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API key")

    user = await user_repo.get_by_id(api_key.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    await api_key_repo.update_last_used(api_key.id)
    return user


# ── RBAC helpers ──────────────────────────────────────────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]


def require_org_membership(required_role: str | None = None):
    """
    Returns a FastAPI dependency that resolves the org membership for
    the current user in :org_slug. Raises 403 if role is insufficient.
    """
    async def _dep(
        org_slug: str,
        current_user: CurrentUser,
        member_repo: OrgMemberRepository = Depends(get_member_repo),
        session: SessionDep = None,
    ) -> OrgMember:
        from src.infrastructure.database.repositories import PostgresOrganizationRepository
        org_repo = PostgresOrganizationRepository(session)  # type: ignore[arg-type]
        org = await org_repo.get_by_slug(org_slug)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Organization '{org_slug}' not found")

        member = await member_repo.get(org.id, current_user.id)
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")

        if required_role:
            _ROLE_RANK = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}
            if _ROLE_RANK.get(member.role, -1) < _ROLE_RANK.get(required_role, 99):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' or higher is required",
                )
        return member

    return _dep


# Convenience typed dependencies
OrgMemberDep = Annotated[OrgMember, Depends(require_org_membership())]
OrgAdminDep = Annotated[OrgMember, Depends(require_org_membership("admin"))]
OrgOwnerDep = Annotated[OrgMember, Depends(require_org_membership("owner"))]


def require_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required")
    return current_user

"""API key management routes."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.use_cases.api_keys import (
    ApiKeyNotFoundError,
    CreateApiKeyDTO,
    CreateApiKeyUseCase,
    CreatedApiKeyDTO,
    ListApiKeysUseCase,
    RevokeApiKeyUseCase,
)
from src.infrastructure.database.repositories import (
    PostgresApiKeyRepository,
    PostgresOrgMemberRepository,
    PostgresOrganizationRepository,
)
from src.presentation.api.auth_dependencies import (
    CurrentUser, OrgAdminDep, OrgMemberDep, SessionDep,
)

router = APIRouter(prefix="/organizations/{org_slug}/api-keys", tags=["api-keys"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default=["read", "write"])


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class CreatedApiKeyResponse(ApiKeyResponse):
    raw_key: str  # shown exactly once


# ── Endpoints ─────────────────────────────────────────────────────────────────

async def _get_org_id(org_slug: str, session) -> str:
    org = await PostgresOrganizationRepository(session).get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org.id


@router.post("", response_model=CreatedApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    org_slug: str,
    body: CreateApiKeyRequest,
    current_user: CurrentUser,
    org_admin: OrgAdminDep,
    session: SessionDep,
) -> CreatedApiKeyResponse:
    org_id = await _get_org_id(org_slug, session)
    uc = CreateApiKeyUseCase(
        key_repo=PostgresApiKeyRepository(session),
        member_repo=PostgresOrgMemberRepository(session),
    )
    result: CreatedApiKeyDTO = await uc.execute(CreateApiKeyDTO(
        org_id=org_id, user_id=current_user.id,
        name=body.name, scopes=body.scopes,
    ))
    k = result.api_key
    return CreatedApiKeyResponse(
        id=k.id, name=k.name, key_prefix=k.key_prefix, scopes=k.scopes,
        last_used_at=k.last_used_at, expires_at=k.expires_at,
        created_at=k.created_at, raw_key=result.raw_key,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> list[ApiKeyResponse]:
    org_id = await _get_org_id(org_slug, session)
    uc = ListApiKeysUseCase(key_repo=PostgresApiKeyRepository(session))
    keys = await uc.execute(org_id)
    return [
        ApiKeyResponse(
            id=k.id, name=k.name, key_prefix=k.key_prefix, scopes=k.scopes,
            last_used_at=k.last_used_at, expires_at=k.expires_at, created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    org_slug: str,
    key_id: str,
    current_user: CurrentUser,
    org_admin: OrgAdminDep,
    session: SessionDep,
) -> None:
    org_id = await _get_org_id(org_slug, session)
    uc = RevokeApiKeyUseCase(
        key_repo=PostgresApiKeyRepository(session),
        member_repo=PostgresOrgMemberRepository(session),
    )
    try:
        await uc.execute(key_id=key_id, org_id=org_id, user_id=current_user.id)
    except ApiKeyNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

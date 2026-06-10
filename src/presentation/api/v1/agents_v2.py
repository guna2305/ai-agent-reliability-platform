"""Agent Registry v2 routes — org-scoped, versioned agents."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.application.use_cases.agents_v2 import (
    AgentV2NotFoundError,
    AgentVersionNotFoundError,
    CreateAgentV2DTO,
    CreateAgentV2UseCase,
    CreateAgentVersionUseCase,
    CreateVersionDTO,
    DeleteAgentV2UseCase,
    GetAgentV2UseCase,
    ListAgentsV2UseCase,
    ListAgentVersionsUseCase,
    PromoteVersionUseCase,
    UpdateAgentV2DTO,
    UpdateAgentV2UseCase,
)
from src.infrastructure.database.repositories import (
    PostgresAgentV2Repository,
    PostgresAgentVersionRepository,
    PostgresOrganizationRepository,
)
from src.presentation.api.auth_dependencies import (
    CurrentUser,
    OrgAdminDep,
    OrgMemberDep,
    SessionDep,
)

router = APIRouter(prefix="/organizations/{org_slug}/agents", tags=["agents"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    agent_type: str = Field(default="custom")
    framework: str = Field(default="custom")
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateAgentRequest(BaseModel):
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(active|inactive|deprecated)$")
    tags: list[str] | None = None
    framework: str | None = None


class AgentResponse(BaseModel):
    id: str
    org_id: str
    name: str
    slug: str
    description: str | None
    agent_type: str
    framework: str
    status: str
    tags: list[str]
    created_by: str
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    items: list[AgentResponse]
    total: int
    limit: int
    offset: int


class CreateVersionRequest(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    system_prompt: str | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)


class AgentVersionResponse(BaseModel):
    id: str
    agent_id: str
    version: str
    version_number: int
    description: str | None
    config: dict[str, Any]
    system_prompt: str | None
    tools: list[dict[str, Any]]
    is_production: bool
    created_by: str
    created_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _resolve_org_id(org_slug: str, session) -> str:
    org = await PostgresOrganizationRepository(session).get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_slug}' not found")
    return org.id


def _agent_response(d: dict) -> AgentResponse:
    return AgentResponse(**d)


# ── CRUD Endpoints ────────────────────────────────────────────────────────────

@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    org_slug: str,
    body: CreateAgentRequest,
    current_user: CurrentUser,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> AgentResponse:
    org_id = await _resolve_org_id(org_slug, session)
    uc = CreateAgentV2UseCase(PostgresAgentV2Repository(session))
    agent = await uc.execute(CreateAgentV2DTO(
        org_id=org_id,
        name=body.name,
        created_by=current_user.id,
        description=body.description,
        agent_type=body.agent_type,
        framework=body.framework,
        tags=body.tags,
        metadata=body.metadata,
    ))
    return _agent_response(agent)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    agent_status: str | None = Query(default=None, alias="status"),
    agent_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AgentListResponse:
    org_id = await _resolve_org_id(org_slug, session)
    uc = ListAgentsV2UseCase(PostgresAgentV2Repository(session))
    agents, total = await uc.execute(
        org_id=org_id, status=agent_status, agent_type=agent_type,
        limit=limit, offset=offset,
    )
    return AgentListResponse(
        items=[_agent_response(a) for a in agents],
        total=total, limit=limit, offset=offset,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    org_slug: str,
    agent_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> AgentResponse:
    org_id = await _resolve_org_id(org_slug, session)
    uc = GetAgentV2UseCase(PostgresAgentV2Repository(session))
    try:
        agent = await uc.execute(agent_id, org_id)
    except AgentV2NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _agent_response(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    org_slug: str,
    agent_id: str,
    body: UpdateAgentRequest,
    org_member: OrgAdminDep,
    session: SessionDep,
) -> AgentResponse:
    org_id = await _resolve_org_id(org_slug, session)
    uc = UpdateAgentV2UseCase(PostgresAgentV2Repository(session))
    try:
        agent = await uc.execute(
            agent_id, org_id,
            UpdateAgentV2DTO(
                description=body.description,
                status=body.status,
                tags=body.tags,
                framework=body.framework,
            ),
        )
    except AgentV2NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _agent_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    org_slug: str,
    agent_id: str,
    org_member: OrgAdminDep,
    session: SessionDep,
) -> None:
    org_id = await _resolve_org_id(org_slug, session)
    uc = DeleteAgentV2UseCase(PostgresAgentV2Repository(session))
    try:
        await uc.execute(agent_id, org_id)
    except AgentV2NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


# ── Version Endpoints ─────────────────────────────────────────────────────────

@router.post("/{agent_id}/versions", response_model=AgentVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    org_slug: str,
    agent_id: str,
    body: CreateVersionRequest,
    current_user: CurrentUser,
    org_member: OrgAdminDep,
    session: SessionDep,
) -> AgentVersionResponse:
    org_id = await _resolve_org_id(org_slug, session)
    uc = CreateAgentVersionUseCase(
        agent_repo=PostgresAgentV2Repository(session),
        version_repo=PostgresAgentVersionRepository(session),
    )
    try:
        version = await uc.execute(org_id, CreateVersionDTO(
            agent_id=agent_id,
            version=body.version,
            created_by=current_user.id,
            config=body.config,
            system_prompt=body.system_prompt,
            tools=body.tools,
            description=body.description,
        ))
    except AgentV2NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return AgentVersionResponse(**version.__dict__)


@router.get("/{agent_id}/versions", response_model=list[AgentVersionResponse])
async def list_versions(
    org_slug: str,
    agent_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> list[AgentVersionResponse]:
    uc = ListAgentVersionsUseCase(PostgresAgentVersionRepository(session))
    versions = await uc.execute(agent_id)
    return [AgentVersionResponse(**v.__dict__) for v in versions]


@router.post("/{agent_id}/versions/{version_id}/promote", response_model=AgentVersionResponse)
async def promote_version(
    org_slug: str,
    agent_id: str,
    version_id: str,
    org_member: OrgAdminDep,
    session: SessionDep,
) -> AgentVersionResponse:
    org_id = await _resolve_org_id(org_slug, session)
    uc = PromoteVersionUseCase(
        agent_repo=PostgresAgentV2Repository(session),
        version_repo=PostgresAgentVersionRepository(session),
    )
    try:
        version = await uc.execute(version_id=version_id, agent_id=agent_id, org_id=org_id)
    except (AgentV2NotFoundError, AgentVersionNotFoundError) as e:
        raise HTTPException(status_code=404, detail=e.message)
    return AgentVersionResponse(**version.__dict__)

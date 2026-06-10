"""Organization management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.use_cases.organizations import (
    CreateOrgDTO,
    CreateOrganizationUseCase,
    InviteMemberDTO,
    InviteMemberUseCase,
    ListOrganizationsUseCase,
    OrgNotFoundError,
    InsufficientPermissionError,
)
from src.infrastructure.database.repositories import (
    PostgresOrganizationRepository,
    PostgresOrgMemberRepository,
    PostgresUserRepository,
)
from src.presentation.api.auth_dependencies import (
    CurrentUser, OrgAdminDep, SessionDep,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class OrgResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    plan: str
    created_at: str

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    user_id: str
    role: str
    org_id: str


class InviteRequest(BaseModel):
    email: str
    role: str = Field(default="member", pattern="^(owner|admin|member|viewer)$")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: CreateOrgRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> OrgResponse:
    uc = CreateOrganizationUseCase(
        org_repo=PostgresOrganizationRepository(session),
        member_repo=PostgresOrgMemberRepository(session),
    )
    org = await uc.execute(CreateOrgDTO(
        name=body.name,
        description=body.description,
        user_id=current_user.id,
    ))
    return OrgResponse(
        id=org.id, name=org.name, slug=org.slug,
        description=org.description, plan=org.plan,
        created_at=org.created_at.isoformat(),
    )


@router.get("", response_model=list[OrgResponse])
async def list_organizations(
    current_user: CurrentUser,
    session: SessionDep,
) -> list[OrgResponse]:
    uc = ListOrganizationsUseCase(org_repo=PostgresOrganizationRepository(session))
    orgs = await uc.execute(current_user.id)
    return [
        OrgResponse(id=o.id, name=o.name, slug=o.slug,
                    description=o.description, plan=o.plan,
                    created_at=o.created_at.isoformat())
        for o in orgs
    ]


@router.get("/{org_slug}", response_model=OrgResponse)
async def get_organization(
    org_slug: str,
    current_user: CurrentUser,
    session: SessionDep,
) -> OrgResponse:
    org_repo = PostgresOrganizationRepository(session)
    org = await org_repo.get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_slug}' not found")
    member = await PostgresOrgMemberRepository(session).get(org.id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    return OrgResponse(
        id=org.id, name=org.name, slug=org.slug,
        description=org.description, plan=org.plan,
        created_at=org.created_at.isoformat(),
    )


@router.post("/{org_slug}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_slug: str,
    body: InviteRequest,
    org_admin: OrgAdminDep,
    current_user: CurrentUser,
    session: SessionDep,
) -> MemberResponse:
    org_repo = PostgresOrganizationRepository(session)
    org = await org_repo.get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    uc = InviteMemberUseCase(
        org_repo=org_repo,
        member_repo=PostgresOrgMemberRepository(session),
        user_repo=PostgresUserRepository(session),
    )
    try:
        member = await uc.execute(InviteMemberDTO(
            org_id=org.id,
            email=body.email,
            role=body.role,
            inviter_id=current_user.id,
        ))
    except InsufficientPermissionError as e:
        raise HTTPException(status_code=403, detail=e.message)

    return MemberResponse(user_id=member.user_id, role=member.role, org_id=member.org_id)

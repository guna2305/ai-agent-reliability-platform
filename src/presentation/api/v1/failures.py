"""Failure analytics routes — list, search, cluster, resolve, breakdown."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.application.use_cases.failures import (
    ClusterFailuresUseCase,
    FailureAnalyticsUseCase,
    FailureReportNotFoundError,
    GetFailureUseCase,
    ListFailuresUseCase,
    ResolveFailureUseCase,
    SearchFailuresUseCase,
)
from src.domain.value_objects import FailureType
from src.infrastructure.database.repositories import (
    PostgresFailureReportRepository,
    PostgresOrganizationRepository,
)
from src.presentation.api.auth_dependencies import OrgAdminDep, OrgMemberDep, SessionDep

router = APIRouter(prefix="/organizations/{org_slug}/failures", tags=["failures"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class FailureResponse(BaseModel):
    id: str
    org_id: str
    execution_id: str
    failure_type: str
    severity: str
    title: str
    description: str
    root_cause: str | None
    cluster_id: int | None
    is_resolved: bool
    resolution_notes: str | None
    created_at: datetime


class FailureListResponse(BaseModel):
    items: list[FailureResponse]
    total: int
    limit: int
    offset: int


class ResolveRequest(BaseModel):
    notes: str = Field(..., min_length=1)


class ClusterResponse(BaseModel):
    clustered: int
    newly_embedded: int
    k: int


class SearchResultItem(BaseModel):
    failure: FailureResponse
    score: float


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _org_id(org_slug: str, session) -> str:
    org = await PostgresOrganizationRepository(session).get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_slug}' not found")
    return org.id


def _resp(r) -> FailureResponse:
    return FailureResponse(
        id=r.id, org_id=r.org_id, execution_id=r.execution_id,
        failure_type=r.failure_type.value, severity=r.severity.value,
        title=r.title, description=r.description, root_cause=r.root_cause,
        cluster_id=r.cluster_id, is_resolved=r.is_resolved,
        resolution_notes=r.resolution_notes, created_at=r.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=FailureListResponse)
async def list_failures(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    failure_type: str | None = Query(default=None),
    cluster_id: int | None = Query(default=None),
    is_resolved: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> FailureListResponse:
    org_id = await _org_id(org_slug, session)
    ftype = FailureType(failure_type) if failure_type else None
    uc = ListFailuresUseCase(PostgresFailureReportRepository(session))
    items, total = await uc.execute(org_id, ftype, cluster_id, is_resolved, limit, offset)
    return FailureListResponse(
        items=[_resp(r) for r in items], total=total, limit=limit, offset=offset,
    )


@router.get("/breakdown")
async def type_breakdown(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> list[dict]:
    org_id = await _org_id(org_slug, session)
    uc = FailureAnalyticsUseCase(PostgresFailureReportRepository(session))
    return await uc.type_breakdown(org_id)


@router.get("/clusters")
async def cluster_summary(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> list[dict]:
    org_id = await _org_id(org_slug, session)
    uc = FailureAnalyticsUseCase(PostgresFailureReportRepository(session))
    return await uc.cluster_summary(org_id)


@router.post("/cluster", response_model=ClusterResponse)
async def run_clustering(
    org_slug: str,
    org_admin: OrgAdminDep,
    session: SessionDep,
    k: int | None = Query(default=None, ge=1, le=20),
) -> ClusterResponse:
    """Backfill embeddings (Ollama) and re-cluster the org's failures (synchronous)."""
    org_id = await _org_id(org_slug, session)
    uc = ClusterFailuresUseCase(PostgresFailureReportRepository(session))
    result = await uc.execute(org_id, k=k)
    return ClusterResponse(clustered=result.clustered, newly_embedded=result.embedded, k=result.k)


@router.get("/search", response_model=list[SearchResultItem])
async def search_failures(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    q: str = Query(..., min_length=1),
    top_k: int = Query(default=10, ge=1, le=50),
) -> list[SearchResultItem]:
    """Semantic search over failures by cosine similarity to the query embedding."""
    org_id = await _org_id(org_slug, session)
    uc = SearchFailuresUseCase(PostgresFailureReportRepository(session))
    results = await uc.execute(org_id, q, top_k)
    return [SearchResultItem(failure=_resp(r), score=score) for r, score in results]


@router.get("/{report_id}", response_model=FailureResponse)
async def get_failure(
    org_slug: str,
    report_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> FailureResponse:
    org_id = await _org_id(org_slug, session)
    uc = GetFailureUseCase(PostgresFailureReportRepository(session))
    try:
        report = await uc.execute(report_id, org_id)
    except FailureReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _resp(report)


@router.post("/{report_id}/resolve", response_model=FailureResponse)
async def resolve_failure(
    org_slug: str,
    report_id: str,
    body: ResolveRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> FailureResponse:
    org_id = await _org_id(org_slug, session)
    uc = ResolveFailureUseCase(PostgresFailureReportRepository(session))
    try:
        report = await uc.execute(report_id, org_id, body.notes)
    except FailureReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _resp(report)

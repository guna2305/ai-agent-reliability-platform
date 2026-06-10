"""Analytics routes: execution stats, cost summary, model pricing."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.application.use_cases.executions import (
    AnalyticsQuery,
    GetCostSummaryUseCase,
    GetExecutionStatsUseCase,
)
from src.infrastructure.ai.cost_calculator import get_supported_models
from src.infrastructure.database.repositories import (
    PostgresExecutionRepository,
    PostgresOrganizationRepository,
)
from src.presentation.api.auth_dependencies import OrgMemberDep, SessionDep

router = APIRouter(prefix="/organizations/{org_slug}/analytics", tags=["analytics"])


async def _org_id(org_slug: str, session) -> str:
    org = await PostgresOrganizationRepository(session).get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_slug}' not found")
    return org.id


@router.get("/executions")
async def execution_stats(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    days: int = Query(default=30, ge=1, le=365),
    agent_id: str | None = Query(default=None),
):
    org_id = await _org_id(org_slug, session)
    uc = GetExecutionStatsUseCase(PostgresExecutionRepository(session))
    return await uc.execute(AnalyticsQuery(org_id=org_id, days=days, agent_id=agent_id))


@router.get("/costs")
async def cost_summary(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    days: int = Query(default=30, ge=1, le=365),
):
    org_id = await _org_id(org_slug, session)
    uc = GetCostSummaryUseCase(PostgresExecutionRepository(session))
    return await uc.execute(AnalyticsQuery(org_id=org_id, days=days))


@router.get("/models")
async def supported_models(org_member: OrgMemberDep, org_slug: str):
    """Return all supported models and their pricing (Ollama = free)."""
    return get_supported_models()

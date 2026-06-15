"""Hallucination detection routes."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.application.use_cases.hallucinations import (
    ConfirmHallucinationUseCase,
    DetectAndSaveUseCase,
    DetectionRequest,
    HallucinationReportNotFoundError,
    ListFlaggedHallucinationsUseCase,
    ListHallucinationsByExecutionUseCase,
)
from src.infrastructure.database.repositories import (
    PostgresExecutionRepository,
    PostgresHallucinationReportRepository,
    PostgresOrganizationRepository,
)
from src.presentation.api.auth_dependencies import OrgAdminDep, OrgMemberDep, SessionDep

router = APIRouter(prefix="/organizations/{org_slug}", tags=["hallucinations"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class DetectRequest(BaseModel):
    question: str = Field(default="", description="The user question/prompt")
    response: str = Field(..., min_length=1, description="The agent response to check")
    reference: str | None = Field(default=None, description="Known-good reference answer")
    context_chunks: list[str] = Field(default_factory=list, description="Retrieved context")


class HallucinationResponse(BaseModel):
    id: str
    execution_id: str
    eval_result_id: str | None
    hallucination_score: str
    confidence: str
    detection_method: str
    flagged_segments: list[dict[str, Any]]
    reasoning: str | None
    is_confirmed: bool
    is_hallucinated: bool
    created_at: datetime


class HallucinationListResponse(BaseModel):
    items: list[HallucinationResponse]
    total: int
    limit: int
    offset: int


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _org_id(org_slug: str, session) -> str:
    org = await PostgresOrganizationRepository(session).get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_slug}' not found")
    return org.id


def _response(r) -> HallucinationResponse:
    return HallucinationResponse(
        id=r.id,
        execution_id=r.execution_id,
        eval_result_id=r.eval_result_id,
        hallucination_score=str(r.hallucination_score),
        confidence=str(r.confidence),
        detection_method=r.detection_method.value,
        flagged_segments=r.flagged_segments,
        reasoning=r.reasoning,
        is_confirmed=r.is_confirmed,
        is_hallucinated=r.is_hallucinated,
        created_at=r.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/executions/{exec_id}/hallucination-check",
    response_model=HallucinationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def detect_hallucination(
    org_slug: str,
    exec_id: str,
    body: DetectRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> HallucinationResponse:
    """Run hallucination detection synchronously and store the report.

    For async detection on completed executions, the platform also dispatches
    `hallucinations.detect` via Celery; this endpoint is the on-demand path.
    """
    org_id = await _org_id(org_slug, session)
    execution = await PostgresExecutionRepository(session).get_by_id(exec_id)
    if not execution or execution.org_id != org_id:
        raise HTTPException(status_code=404, detail=f"Execution '{exec_id}' not found")

    uc = DetectAndSaveUseCase(PostgresHallucinationReportRepository(session))
    report = await uc.execute(DetectionRequest(
        execution_id=exec_id,
        question=body.question,
        response=body.response,
        reference=body.reference,
        context_chunks=body.context_chunks,
    ))
    return _response(report)


@router.get("/executions/{exec_id}/hallucinations", response_model=list[HallucinationResponse])
async def list_for_execution(
    org_slug: str,
    exec_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> list[HallucinationResponse]:
    uc = ListHallucinationsByExecutionUseCase(PostgresHallucinationReportRepository(session))
    reports = await uc.execute(exec_id)
    return [_response(r) for r in reports]


@router.get("/hallucinations", response_model=HallucinationListResponse)
async def list_flagged(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    min_score: float = Query(default=0.7, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> HallucinationListResponse:
    org_id = await _org_id(org_slug, session)
    uc = ListFlaggedHallucinationsUseCase(PostgresHallucinationReportRepository(session))
    reports, total = await uc.execute(org_id, min_score, limit, offset)
    return HallucinationListResponse(
        items=[_response(r) for r in reports], total=total, limit=limit, offset=offset,
    )


@router.post("/hallucinations/{report_id}/confirm", response_model=HallucinationResponse)
async def confirm_hallucination(
    org_slug: str,
    report_id: str,
    org_admin: OrgAdminDep,
    session: SessionDep,
) -> HallucinationResponse:
    uc = ConfirmHallucinationUseCase(PostgresHallucinationReportRepository(session))
    try:
        report = await uc.execute(report_id)
    except HallucinationReportNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _response(report)

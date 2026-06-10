"""Evaluation run routes — launch eval jobs, retrieve results."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.application.use_cases.evaluations import (
    CreateEvaluationRunDTO,
    CreateEvaluationRunUseCase,
    EvaluationRunNotFoundError,
    GetEvaluationResultsUseCase,
    GetEvaluationRunUseCase,
    ListEvaluationRunsUseCase,
)
from src.infrastructure.database.repositories import (
    PostgresEvaluationResultRepository,
    PostgresEvaluationRunRepository,
    PostgresOrganizationRepository,
)
from src.presentation.api.auth_dependencies import (
    CurrentUser,
    OrgMemberDep,
    SessionDep,
)

router = APIRouter(prefix="/organizations/{org_slug}/evaluations", tags=["evaluations"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateEvalRunRequest(BaseModel):
    agent_id: str
    name: str = Field(..., min_length=1, max_length=255)
    eval_type: str = Field(..., pattern="^(llm_judge|ground_truth|rag|custom)$")
    dataset_id: str | None = None
    agent_version_id: str | None = None
    description: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class EvalRunResponse(BaseModel):
    id: str
    org_id: str
    agent_id: str
    dataset_id: str | None
    name: str
    status: str
    eval_type: str
    total_items: int
    completed_items: int
    failed_items: int
    aggregate_scores: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class EvalRunListResponse(BaseModel):
    items: list[EvalRunResponse]
    total: int
    limit: int
    offset: int


class EvalResultResponse(BaseModel):
    id: str
    eval_run_id: str
    execution_id: str | None
    dataset_item_id: str | None
    correctness_score: str | None
    relevance_score: str | None
    faithfulness_score: str | None
    helpfulness_score: str | None
    hallucination_score: str | None
    context_precision: str | None
    context_recall: str | None
    answer_relevancy: str | None
    reasoning: str | None
    passed: bool
    created_at: datetime


class EvalResultListResponse(BaseModel):
    items: list[EvalResultResponse]
    total: int
    limit: int
    offset: int


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _org_id(org_slug: str, session) -> str:
    org = await PostgresOrganizationRepository(session).get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_slug}' not found")
    return org.id


def _run_response(r) -> EvalRunResponse:
    return EvalRunResponse(
        id=r.id, org_id=r.org_id, agent_id=r.agent_id, dataset_id=r.dataset_id,
        name=r.name, status=r.status.value, eval_type=r.eval_type.value,
        total_items=r.total_items, completed_items=r.completed_items,
        failed_items=r.failed_items, aggregate_scores=r.aggregate_scores,
        started_at=r.started_at, completed_at=r.completed_at, created_at=r.created_at,
    )


def _dec(v) -> str | None:
    return str(v) if v is not None else None


def _result_response(r) -> EvalResultResponse:
    return EvalResultResponse(
        id=r.id, eval_run_id=r.eval_run_id, execution_id=r.execution_id,
        dataset_item_id=r.dataset_item_id,
        correctness_score=_dec(r.correctness_score), relevance_score=_dec(r.relevance_score),
        faithfulness_score=_dec(r.faithfulness_score), helpfulness_score=_dec(r.helpfulness_score),
        hallucination_score=_dec(r.hallucination_score), context_precision=_dec(r.context_precision),
        context_recall=_dec(r.context_recall), answer_relevancy=_dec(r.answer_relevancy),
        reasoning=r.reasoning, passed=r.passed, created_at=r.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/runs", response_model=EvalRunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    org_slug: str,
    body: CreateEvalRunRequest,
    current_user: CurrentUser,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> EvalRunResponse:
    org_id = await _org_id(org_slug, session)
    uc = CreateEvaluationRunUseCase(PostgresEvaluationRunRepository(session))
    run = await uc.execute(CreateEvaluationRunDTO(
        org_id=org_id, agent_id=body.agent_id, created_by=current_user.id,
        name=body.name, eval_type=body.eval_type, dataset_id=body.dataset_id,
        agent_version_id=body.agent_version_id, description=body.description,
        config=body.config,
    ))

    # Dispatch the evaluation to Celery (best-effort; run stays PENDING if broker down)
    try:
        from src.infrastructure.queue.tasks.evaluation_tasks import run_evaluation
        run_evaluation.delay(run.id)
    except Exception:
        pass

    return _run_response(run)


@router.get("/runs", response_model=EvalRunListResponse)
async def list_runs(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    agent_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> EvalRunListResponse:
    org_id = await _org_id(org_slug, session)
    uc = ListEvaluationRunsUseCase(PostgresEvaluationRunRepository(session))
    runs, total = await uc.execute(org_id, agent_id, limit, offset)
    return EvalRunListResponse(
        items=[_run_response(r) for r in runs], total=total, limit=limit, offset=offset,
    )


@router.get("/runs/{run_id}", response_model=EvalRunResponse)
async def get_run(
    org_slug: str,
    run_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> EvalRunResponse:
    org_id = await _org_id(org_slug, session)
    uc = GetEvaluationRunUseCase(PostgresEvaluationRunRepository(session))
    try:
        run = await uc.execute(run_id, org_id)
    except EvaluationRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _run_response(run)


@router.get("/runs/{run_id}/results", response_model=EvalResultListResponse)
async def get_results(
    org_slug: str,
    run_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    passed: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> EvalResultListResponse:
    org_id = await _org_id(org_slug, session)
    # Validate run ownership first
    run_uc = GetEvaluationRunUseCase(PostgresEvaluationRunRepository(session))
    try:
        await run_uc.execute(run_id, org_id)
    except EvaluationRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

    uc = GetEvaluationResultsUseCase(PostgresEvaluationResultRepository(session))
    results, total = await uc.execute(run_id, passed, limit, offset)
    return EvalResultListResponse(
        items=[_result_response(r) for r in results], total=total, limit=limit, offset=offset,
    )

"""Execution Engine API routes."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.application.use_cases.executions import (
    CancelExecutionUseCase,
    CloseSpanDTO,
    CloseSpanUseCase,
    CompleteExecutionDTO,
    CompleteExecutionUseCase,
    CreateExecutionDTO,
    CreateExecutionUseCase,
    ExecutionAccessDeniedError,
    ExecutionNotFoundError,
    FailExecutionDTO,
    FailExecutionUseCase,
    FailSpanDTO,
    FailSpanUseCase,
    GetExecutionUseCase,
    GetTraceTreeUseCase,
    ListExecutionsQuery,
    ListExecutionsUseCase,
    ListToolCallsUseCase,
    OpenSpanDTO,
    OpenSpanUseCase,
    RecordToolCallDTO,
    RecordToolCallUseCase,
    StartExecutionUseCase,
    TraceNotFoundError,
)
from src.domain.exceptions import DomainException
from src.domain.value_objects import ExecutionStatus, TriggerType, TraceType
from src.infrastructure.database.repositories import (
    PostgresExecutionRepository,
    PostgresExecutionTraceRepository,
    PostgresOrganizationRepository,
    PostgresToolCallRepository,
)
from src.presentation.api.auth_dependencies import (
    CurrentUser, OrgMemberDep, SessionDep,
)

router = APIRouter(prefix="/organizations/{org_slug}/executions", tags=["executions"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateExecutionRequest(BaseModel):
    agent_id: str
    input: dict[str, Any]
    agent_version_id: str | None = None
    trigger_type: str = "api"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompleteExecutionRequest(BaseModel):
    output: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = "ollama"
    model: str = "llama3.2"


class FailExecutionRequest(BaseModel):
    error_message: str = Field(..., min_length=1)


class ExecutionResponse(BaseModel):
    id: str
    org_id: str
    agent_id: str
    agent_version_id: str | None
    status: str
    trigger_type: str
    input: dict[str, Any]
    output: dict[str, Any] | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    total_tokens: int | None
    input_tokens: int | None
    output_tokens: int | None
    total_cost_usd: str | None
    model_provider: str | None
    model_name: str | None
    tags: list[str]


class ExecutionListResponse(BaseModel):
    items: list[ExecutionResponse]
    total: int
    limit: int
    offset: int


class OpenSpanRequest(BaseModel):
    trace_type: str
    name: str
    input: dict[str, Any]
    sequence_order: int
    parent_trace_id: str | None = None
    model: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CloseSpanRequest(BaseModel):
    output: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = "ollama"
    model: str = "llama3.2"


class RecordToolCallRequest(BaseModel):
    tool_name: str
    tool_type: str = "custom"
    input: dict[str, Any]
    trace_id: str | None = None


class ToolCallCompleteRequest(BaseModel):
    output: dict[str, Any]


class ToolCallFailRequest(BaseModel):
    error: str


# ── Helper ────────────────────────────────────────────────────────────────────

async def _org_id(org_slug: str, session) -> str:
    org = await PostgresOrganizationRepository(session).get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_slug}' not found")
    return org.id


def _exec_response(e) -> ExecutionResponse:
    return ExecutionResponse(
        id=e.id, org_id=e.org_id, agent_id=e.agent_id,
        agent_version_id=e.agent_version_id, status=e.status.value,
        trigger_type=e.trigger_type.value, input=e.input, output=e.output,
        error_message=e.error_message, started_at=e.started_at,
        completed_at=e.completed_at, duration_ms=e.duration_ms,
        total_tokens=e.total_tokens, input_tokens=e.input_tokens,
        output_tokens=e.output_tokens,
        total_cost_usd=str(e.total_cost_usd) if e.total_cost_usd else None,
        model_provider=e.model_provider, model_name=e.model_name, tags=e.tags,
    )


# ── Execution lifecycle endpoints ─────────────────────────────────────────────

@router.post("", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def create_execution(
    org_slug: str,
    body: CreateExecutionRequest,
    current_user: CurrentUser,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> ExecutionResponse:
    org_id = await _org_id(org_slug, session)
    uc = CreateExecutionUseCase(PostgresExecutionRepository(session))
    execution = await uc.execute(CreateExecutionDTO(
        org_id=org_id,
        agent_id=body.agent_id,
        input=body.input,
        initiated_by=current_user.id,
        agent_version_id=body.agent_version_id,
        trigger_type=TriggerType(body.trigger_type),
        tags=body.tags,
        metadata=body.metadata,
    ))
    return _exec_response(execution)


@router.get("", response_model=ExecutionListResponse)
async def list_executions(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    agent_id: str | None = Query(default=None),
    exec_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ExecutionListResponse:
    org_id = await _org_id(org_slug, session)
    uc = ListExecutionsUseCase(PostgresExecutionRepository(session))
    status_filter = ExecutionStatus(exec_status) if exec_status else None
    items, total = await uc.execute(ListExecutionsQuery(
        org_id=org_id, agent_id=agent_id, status=status_filter,
        limit=limit, offset=offset,
    ))
    return ExecutionListResponse(
        items=[_exec_response(e) for e in items],
        total=total, limit=limit, offset=offset,
    )


@router.get("/{exec_id}", response_model=ExecutionResponse)
async def get_execution(
    org_slug: str,
    exec_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> ExecutionResponse:
    org_id = await _org_id(org_slug, session)
    uc = GetExecutionUseCase(PostgresExecutionRepository(session))
    try:
        execution = await uc.execute(exec_id, org_id)
    except (ExecutionNotFoundError, ExecutionAccessDeniedError) as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _exec_response(execution)


@router.post("/{exec_id}/start", response_model=ExecutionResponse)
async def start_execution(
    org_slug: str,
    exec_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> ExecutionResponse:
    org_id = await _org_id(org_slug, session)
    uc = StartExecutionUseCase(PostgresExecutionRepository(session))
    try:
        execution = await uc.execute(exec_id, org_id)
    except (ExecutionNotFoundError, ExecutionAccessDeniedError) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DomainException as e:
        raise HTTPException(status_code=422, detail=e.message)
    return _exec_response(execution)


@router.post("/{exec_id}/complete", response_model=ExecutionResponse)
async def complete_execution(
    org_slug: str,
    exec_id: str,
    body: CompleteExecutionRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> ExecutionResponse:
    org_id = await _org_id(org_slug, session)
    uc = CompleteExecutionUseCase(PostgresExecutionRepository(session))
    try:
        execution = await uc.execute(CompleteExecutionDTO(
            exec_id=exec_id, org_id=org_id, output=body.output,
            input_tokens=body.input_tokens, output_tokens=body.output_tokens,
            provider=body.provider, model=body.model,
        ))
    except (ExecutionNotFoundError, ExecutionAccessDeniedError) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DomainException as e:
        raise HTTPException(status_code=422, detail=e.message)
    return _exec_response(execution)


@router.post("/{exec_id}/fail", response_model=ExecutionResponse)
async def fail_execution(
    org_slug: str,
    exec_id: str,
    body: FailExecutionRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> ExecutionResponse:
    org_id = await _org_id(org_slug, session)
    uc = FailExecutionUseCase(PostgresExecutionRepository(session))
    try:
        execution = await uc.execute(FailExecutionDTO(
            exec_id=exec_id, org_id=org_id, error_message=body.error_message,
        ))
    except (ExecutionNotFoundError, ExecutionAccessDeniedError) as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DomainException as e:
        raise HTTPException(status_code=422, detail=e.message)
    return _exec_response(execution)


@router.post("/{exec_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(
    org_slug: str,
    exec_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> ExecutionResponse:
    org_id = await _org_id(org_slug, session)
    uc = CancelExecutionUseCase(PostgresExecutionRepository(session))
    try:
        execution = await uc.execute(exec_id, org_id)
    except (ExecutionNotFoundError, ExecutionAccessDeniedError) as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _exec_response(execution)


# ── Trace (span) endpoints ────────────────────────────────────────────────────

@router.post("/{exec_id}/spans", status_code=status.HTTP_201_CREATED)
async def open_span(
    org_slug: str,
    exec_id: str,
    body: OpenSpanRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> dict:
    uc = OpenSpanUseCase(PostgresExecutionTraceRepository(session))
    span = await uc.execute(OpenSpanDTO(
        execution_id=exec_id,
        trace_type=TraceType(body.trace_type),
        name=body.name,
        input=body.input,
        sequence_order=body.sequence_order,
        parent_trace_id=body.parent_trace_id,
        model=body.model,
        metadata=body.metadata,
    ))
    return {"id": span.id, "span_id": span.span_id, "status": span.status.value}


@router.post("/{exec_id}/spans/{trace_id}/complete")
async def close_span(
    org_slug: str,
    exec_id: str,
    trace_id: str,
    body: CloseSpanRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> dict:
    uc = CloseSpanUseCase(PostgresExecutionTraceRepository(session))
    try:
        span = await uc.execute(CloseSpanDTO(
            trace_id=trace_id, output=body.output,
            input_tokens=body.input_tokens, output_tokens=body.output_tokens,
            provider=body.provider, model=body.model,
        ))
    except TraceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return {"id": span.id, "duration_ms": span.duration_ms, "status": span.status.value}


@router.post("/{exec_id}/spans/{trace_id}/fail")
async def fail_span(
    org_slug: str,
    exec_id: str,
    trace_id: str,
    body: dict,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> dict:
    uc = FailSpanUseCase(PostgresExecutionTraceRepository(session))
    try:
        span = await uc.execute(FailSpanDTO(trace_id=trace_id, error=body.get("error", "")))
    except TraceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return {"id": span.id, "status": span.status.value}


@router.get("/{exec_id}/traces")
async def get_trace_tree(
    org_slug: str,
    exec_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> list[dict]:
    uc = GetTraceTreeUseCase(PostgresExecutionTraceRepository(session))
    return await uc.execute(exec_id)


# ── Tool call endpoints ───────────────────────────────────────────────────────

@router.post("/{exec_id}/tool-calls", status_code=status.HTTP_201_CREATED)
async def record_tool_call(
    org_slug: str,
    exec_id: str,
    body: RecordToolCallRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> dict:
    uc = RecordToolCallUseCase(PostgresToolCallRepository(session))
    call = await uc.record_start(RecordToolCallDTO(
        execution_id=exec_id,
        tool_name=body.tool_name,
        tool_type=body.tool_type,
        input=body.input,
        trace_id=body.trace_id,
    ))
    return {"id": call.id, "status": call.status}


@router.post("/{exec_id}/tool-calls/{call_id}/complete")
async def complete_tool_call(
    org_slug: str,
    exec_id: str,
    call_id: str,
    body: ToolCallCompleteRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> dict:
    uc = RecordToolCallUseCase(PostgresToolCallRepository(session))
    try:
        call = await uc.record_complete(call_id, body.output)
    except DomainException as e:
        raise HTTPException(status_code=404, detail=e.message)
    return {"id": call.id, "status": call.status, "duration_ms": call.duration_ms}


@router.get("/{exec_id}/tool-calls")
async def list_tool_calls(
    org_slug: str,
    exec_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> list[dict]:
    uc = ListToolCallsUseCase(PostgresToolCallRepository(session))
    calls = await uc.execute(exec_id)
    return [
        {
            "id": c.id, "tool_name": c.tool_name, "tool_type": c.tool_type,
            "status": c.status, "duration_ms": c.duration_ms,
            "error_message": c.error_message, "started_at": c.started_at.isoformat(),
        }
        for c in calls
    ]

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.dtos import CompleteRunDTO, FailRunDTO, StartRunDTO
from src.application.use_cases.runs import (
    CompleteRunUseCase,
    FailRunUseCase,
    ListRunsQuery,
    ListRunsUseCase,
    StartRunUseCase,
)
from src.domain.exceptions import (
    AgentNotFoundError,
    AgentRunNotFoundError,
    InvalidAgentStateError,
    InvalidRunTransitionError,
)
from src.domain.value_objects import RunStatus
from src.presentation.api.dependencies import (
    get_complete_run_uc,
    get_fail_run_uc,
    get_list_runs_uc,
    get_start_run_uc,
)
from src.presentation.schemas.run_schemas import (
    AgentRunResponse,
    CompleteRunRequest,
    FailRunRequest,
    RunListResponse,
    StartRunRequest,
)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
async def start_run(
    body: StartRunRequest,
    uc: StartRunUseCase = Depends(get_start_run_uc),
) -> AgentRunResponse:
    try:
        dto = StartRunDTO(agent_id=body.agent_id, metadata=body.metadata)
        result = await uc.execute(dto)
        return AgentRunResponse(**result.__dict__)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InvalidAgentStateError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)


@router.get("", response_model=RunListResponse)
async def list_runs(
    agent_id: str = Query(...),
    run_status: RunStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    uc: ListRunsUseCase = Depends(get_list_runs_uc),
) -> RunListResponse:
    result = await uc.execute(
        ListRunsQuery(agent_id=agent_id, status=run_status, limit=limit, offset=offset)
    )
    return RunListResponse(
        items=[AgentRunResponse(**r.__dict__) for r in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.post("/{run_id}/complete", response_model=AgentRunResponse)
async def complete_run(
    run_id: str,
    body: CompleteRunRequest,
    uc: CompleteRunUseCase = Depends(get_complete_run_uc),
) -> AgentRunResponse:
    try:
        dto = CompleteRunDTO(
            run_id=run_id,
            input_tokens=body.input_tokens,
            output_tokens=body.output_tokens,
        )
        result = await uc.execute(dto)
        return AgentRunResponse(**result.__dict__)
    except AgentRunNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InvalidRunTransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)


@router.post("/{run_id}/fail", response_model=AgentRunResponse)
async def fail_run(
    run_id: str,
    body: FailRunRequest,
    uc: FailRunUseCase = Depends(get_fail_run_uc),
) -> AgentRunResponse:
    try:
        dto = FailRunDTO(run_id=run_id, error_message=body.error_message)
        result = await uc.execute(dto)
        return AgentRunResponse(**result.__dict__)
    except AgentRunNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InvalidRunTransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.dtos import CreateAgentDTO
from src.application.use_cases.agents import (
    CreateAgentUseCase,
    GetAgentUseCase,
    ListAgentsQuery,
    ListAgentsUseCase,
    UpdateAgentStatusUseCase,
)
from src.domain.exceptions import AgentNotFoundError, DuplicateAgentError, InvalidAgentStateError
from src.domain.value_objects import AgentStatus
from src.presentation.api.dependencies import (
    get_create_agent_uc,
    get_get_agent_uc,
    get_list_agents_uc,
    get_update_agent_status_uc,
)
from src.presentation.schemas.agent_schemas import (
    AgentListResponse,
    AgentResponse,
    CreateAgentRequest,
    UpdateAgentStatusRequest,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: CreateAgentRequest,
    uc: CreateAgentUseCase = Depends(get_create_agent_uc),
) -> AgentResponse:
    try:
        dto = CreateAgentDTO(
            name=body.name,
            description=body.description,
            version=body.version,
            tags=body.tags,
        )
        result = await uc.execute(dto)
        return AgentResponse(**result.__dict__)
    except DuplicateAgentError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    agent_status: AgentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    uc: ListAgentsUseCase = Depends(get_list_agents_uc),
) -> AgentListResponse:
    result = await uc.execute(ListAgentsQuery(status=agent_status, limit=limit, offset=offset))
    return AgentListResponse(
        items=[AgentResponse(**a.__dict__) for a in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    uc: GetAgentUseCase = Depends(get_get_agent_uc),
) -> AgentResponse:
    try:
        result = await uc.execute(agent_id)
        return AgentResponse(**result.__dict__)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.patch("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status(
    agent_id: str,
    body: UpdateAgentStatusRequest,
    uc: UpdateAgentStatusUseCase = Depends(get_update_agent_status_uc),
) -> AgentResponse:
    try:
        result = await uc.execute(agent_id, body.status)
        return AgentResponse(**result.__dict__)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except InvalidAgentStateError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)

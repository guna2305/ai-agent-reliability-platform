from src.application.dtos import AgentRunDTO, StartRunDTO
from src.application.interfaces.repositories import AgentRepository, AgentRunRepository
from src.domain.entities import AgentRun
from src.domain.exceptions import AgentNotFoundError, InvalidAgentStateError
from src.domain.value_objects import AgentStatus


class StartRunUseCase:
    def __init__(
        self,
        agent_repo: AgentRepository,
        run_repo: AgentRunRepository,
    ) -> None:
        self._agent_repo = agent_repo
        self._run_repo = run_repo

    async def execute(self, dto: StartRunDTO) -> AgentRunDTO:
        agent = await self._agent_repo.get_by_id(dto.agent_id)
        if not agent:
            raise AgentNotFoundError(dto.agent_id)
        if agent.status != AgentStatus.ACTIVE:
            raise InvalidAgentStateError(agent.id, agent.status.value, "run")

        run = AgentRun.create(agent_id=dto.agent_id, metadata=dto.metadata)
        run.start()
        saved = await self._run_repo.save(run)
        return _to_dto(saved)


def _to_dto(run: AgentRun) -> AgentRunDTO:
    return AgentRunDTO(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        error_message=run.error_message,
        metadata=run.metadata,
    )

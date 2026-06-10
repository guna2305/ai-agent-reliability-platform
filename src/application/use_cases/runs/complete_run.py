from src.application.dtos import AgentRunDTO, CompleteRunDTO
from src.application.interfaces.repositories import AgentRunRepository
from src.domain.entities import AgentRun
from src.domain.exceptions import AgentRunNotFoundError


class CompleteRunUseCase:
    def __init__(self, run_repo: AgentRunRepository) -> None:
        self._run_repo = run_repo

    async def execute(self, dto: CompleteRunDTO) -> AgentRunDTO:
        run = await self._run_repo.get_by_id(dto.run_id)
        if not run:
            raise AgentRunNotFoundError(dto.run_id)

        run.complete(input_tokens=dto.input_tokens, output_tokens=dto.output_tokens)
        updated = await self._run_repo.update(run)
        return _to_dto(updated)


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

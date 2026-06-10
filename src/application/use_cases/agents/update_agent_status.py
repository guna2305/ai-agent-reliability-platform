from src.application.dtos import AgentDTO
from src.application.interfaces.repositories import AgentRepository
from src.domain.entities import Agent
from src.domain.exceptions import AgentNotFoundError
from src.domain.value_objects import AgentStatus


class UpdateAgentStatusUseCase:
    def __init__(self, agent_repo: AgentRepository) -> None:
        self._agent_repo = agent_repo

    async def execute(self, agent_id: str, new_status: AgentStatus) -> AgentDTO:
        agent = await self._agent_repo.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)

        agent.transition_status(new_status)
        updated = await self._agent_repo.update(agent)
        return _to_dto(updated)


def _to_dto(agent: Agent) -> AgentDTO:
    return AgentDTO(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        version=agent.version,
        status=agent.status,
        tags=agent.tags,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )

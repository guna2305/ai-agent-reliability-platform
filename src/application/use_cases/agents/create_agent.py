from src.application.dtos import AgentDTO, CreateAgentDTO
from src.application.interfaces.repositories import AgentRepository
from src.domain.entities import Agent
from src.domain.exceptions import DuplicateAgentError


class CreateAgentUseCase:
    def __init__(self, agent_repo: AgentRepository) -> None:
        self._agent_repo = agent_repo

    async def execute(self, dto: CreateAgentDTO) -> AgentDTO:
        existing = await self._agent_repo.get_by_name(dto.name)
        if existing:
            raise DuplicateAgentError(dto.name)

        agent = Agent.create(
            name=dto.name,
            description=dto.description,
            version=dto.version,
            tags=dto.tags,
        )
        saved = await self._agent_repo.save(agent)
        return _to_dto(saved)


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

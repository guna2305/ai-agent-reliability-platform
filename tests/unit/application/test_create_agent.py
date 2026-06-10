import pytest

from src.application.dtos import CreateAgentDTO
from src.application.interfaces.repositories import AgentRepository
from src.application.use_cases.agents import CreateAgentUseCase
from src.domain.entities import Agent
from src.domain.exceptions import DuplicateAgentError
from src.domain.value_objects import AgentStatus


class InMemoryAgentRepository(AgentRepository):
    def __init__(self) -> None:
        self._store: dict[str, Agent] = {}

    async def save(self, agent: Agent) -> Agent:
        self._store[agent.id] = agent
        return agent

    async def get_by_id(self, agent_id: str) -> Agent | None:
        return self._store.get(agent_id)

    async def get_by_name(self, name: str) -> Agent | None:
        return next((a for a in self._store.values() if a.name == name), None)

    async def list_all(self, status=None, limit=50, offset=0) -> list[Agent]:
        items = list(self._store.values())
        if status:
            items = [a for a in items if a.status == status]
        return items[offset : offset + limit]

    async def update(self, agent: Agent) -> Agent:
        self._store[agent.id] = agent
        return agent

    async def delete(self, agent_id: str) -> bool:
        return self._store.pop(agent_id, None) is not None

    async def count(self, status=None) -> int:
        if status:
            return sum(1 for a in self._store.values() if a.status == status)
        return len(self._store)


@pytest.fixture
def repo() -> InMemoryAgentRepository:
    return InMemoryAgentRepository()


@pytest.fixture
def use_case(repo: InMemoryAgentRepository) -> CreateAgentUseCase:
    return CreateAgentUseCase(repo)


@pytest.mark.asyncio
async def test_create_agent_returns_dto(use_case: CreateAgentUseCase) -> None:
    dto = CreateAgentDTO(name="gpt-agent", description="GPT-based agent", tags=["llm"])
    result = await use_case.execute(dto)

    assert result.name == "gpt-agent"
    assert result.status == AgentStatus.ACTIVE
    assert result.tags == ["llm"]
    assert result.id is not None


@pytest.mark.asyncio
async def test_create_agent_duplicate_raises(use_case: CreateAgentUseCase) -> None:
    dto = CreateAgentDTO(name="my-agent", description="first")
    await use_case.execute(dto)

    with pytest.raises(DuplicateAgentError):
        await use_case.execute(CreateAgentDTO(name="my-agent", description="second"))

import pytest


@pytest.fixture
def agent_factory():
    from src.domain.entities import Agent

    def _make(name: str = "test-agent", description: str = "Test", version: str = "1.0.0") -> Agent:
        return Agent.create(name=name, description=description, version=version)

    return _make


@pytest.fixture
def agent_run_factory():
    from src.domain.entities import AgentRun

    def _make(agent_id: str = "agent-1") -> AgentRun:
        return AgentRun.create(agent_id=agent_id)

    return _make

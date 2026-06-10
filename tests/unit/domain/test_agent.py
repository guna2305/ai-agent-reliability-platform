import pytest

from src.domain.entities import Agent
from src.domain.exceptions import InvalidAgentStateError
from src.domain.value_objects import AgentStatus


def test_create_agent_defaults_to_active():
    agent = Agent.create(name="my-agent", description="desc")
    assert agent.status == AgentStatus.ACTIVE
    assert agent.version == "1.0.0"
    assert agent.tags == []
    assert agent.id is not None


def test_create_agent_with_tags():
    agent = Agent.create(name="tagged", description="d", tags=["llm", "prod"])
    assert agent.tags == ["llm", "prod"]


def test_agent_deactivate():
    agent = Agent.create(name="a", description="d")
    agent.deactivate()
    assert agent.status == AgentStatus.INACTIVE


def test_agent_reactivate():
    agent = Agent.create(name="a", description="d")
    agent.deactivate()
    agent.activate()
    assert agent.status == AgentStatus.ACTIVE


def test_agent_deprecate_from_active():
    agent = Agent.create(name="a", description="d")
    agent.deprecate()
    assert agent.status == AgentStatus.DEPRECATED


def test_agent_cannot_transition_from_deprecated():
    agent = Agent.create(name="a", description="d")
    agent.deprecate()
    with pytest.raises(InvalidAgentStateError):
        agent.activate()


def test_agent_is_operational_only_when_active():
    agent = Agent.create(name="a", description="d")
    assert agent.is_operational is True
    agent.deactivate()
    assert agent.is_operational is False


def test_updated_at_changes_on_transition(agent_factory):
    agent = agent_factory()
    original_updated_at = agent.updated_at
    agent.deactivate()
    assert agent.updated_at > original_updated_at

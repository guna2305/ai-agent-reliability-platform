from src.domain.entities import HealthCheck
from src.domain.value_objects import HealthStatus


def test_create_healthy_check():
    check = HealthCheck.create(
        agent_id="agent-1",
        status=HealthStatus.HEALTHY,
        response_time_ms=42,
        message="All systems go",
    )
    assert check.is_healthy is True
    assert check.response_time_ms == 42
    assert check.agent_id == "agent-1"


def test_create_unhealthy_check():
    check = HealthCheck.create(agent_id="agent-1", status=HealthStatus.UNHEALTHY)
    assert check.is_healthy is False


def test_check_id_is_unique():
    a = HealthCheck.create(agent_id="agent-1", status=HealthStatus.HEALTHY)
    b = HealthCheck.create(agent_id="agent-1", status=HealthStatus.HEALTHY)
    assert a.id != b.id

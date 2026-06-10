from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories import (
    AgentRepository,
    AgentRunRepository,
    HealthCheckRepository,
)
from src.application.use_cases.agents import (
    CreateAgentUseCase,
    GetAgentUseCase,
    ListAgentsUseCase,
    UpdateAgentStatusUseCase,
)
from src.application.use_cases.health_checks import RecordHealthCheckUseCase
from src.application.use_cases.runs import (
    CompleteRunUseCase,
    FailRunUseCase,
    ListRunsUseCase,
    StartRunUseCase,
)
from src.infrastructure.database.connection import get_db_session
from src.infrastructure.database.repositories import (
    PostgresAgentRepository,
    PostgresAgentRunRepository,
    PostgresHealthCheckRepository,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


def get_agent_repo(session: AsyncSession = Depends(get_session)) -> AgentRepository:
    return PostgresAgentRepository(session)


def get_run_repo(session: AsyncSession = Depends(get_session)) -> AgentRunRepository:
    return PostgresAgentRunRepository(session)


def get_health_check_repo(
    session: AsyncSession = Depends(get_session),
) -> HealthCheckRepository:
    return PostgresHealthCheckRepository(session)


def get_create_agent_uc(
    repo: AgentRepository = Depends(get_agent_repo),
) -> CreateAgentUseCase:
    return CreateAgentUseCase(repo)


def get_get_agent_uc(
    repo: AgentRepository = Depends(get_agent_repo),
) -> GetAgentUseCase:
    return GetAgentUseCase(repo)


def get_list_agents_uc(
    repo: AgentRepository = Depends(get_agent_repo),
) -> ListAgentsUseCase:
    return ListAgentsUseCase(repo)


def get_update_agent_status_uc(
    repo: AgentRepository = Depends(get_agent_repo),
) -> UpdateAgentStatusUseCase:
    return UpdateAgentStatusUseCase(repo)


def get_start_run_uc(
    agent_repo: AgentRepository = Depends(get_agent_repo),
    run_repo: AgentRunRepository = Depends(get_run_repo),
) -> StartRunUseCase:
    return StartRunUseCase(agent_repo, run_repo)


def get_complete_run_uc(
    run_repo: AgentRunRepository = Depends(get_run_repo),
) -> CompleteRunUseCase:
    return CompleteRunUseCase(run_repo)


def get_fail_run_uc(
    run_repo: AgentRunRepository = Depends(get_run_repo),
) -> FailRunUseCase:
    return FailRunUseCase(run_repo)


def get_list_runs_uc(
    run_repo: AgentRunRepository = Depends(get_run_repo),
) -> ListRunsUseCase:
    return ListRunsUseCase(run_repo)


def get_record_health_check_uc(
    agent_repo: AgentRepository = Depends(get_agent_repo),
    health_check_repo: HealthCheckRepository = Depends(get_health_check_repo),
) -> RecordHealthCheckUseCase:
    return RecordHealthCheckUseCase(agent_repo, health_check_repo)

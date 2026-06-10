from src.application.dtos import HealthCheckDTO, RecordHealthCheckDTO
from src.application.interfaces.repositories import AgentRepository, HealthCheckRepository
from src.domain.entities import HealthCheck
from src.domain.exceptions import AgentNotFoundError


class RecordHealthCheckUseCase:
    def __init__(
        self,
        agent_repo: AgentRepository,
        health_check_repo: HealthCheckRepository,
    ) -> None:
        self._agent_repo = agent_repo
        self._health_check_repo = health_check_repo

    async def execute(self, dto: RecordHealthCheckDTO) -> HealthCheckDTO:
        agent = await self._agent_repo.get_by_id(dto.agent_id)
        if not agent:
            raise AgentNotFoundError(dto.agent_id)

        check = HealthCheck.create(
            agent_id=dto.agent_id,
            status=dto.status,
            response_time_ms=dto.response_time_ms,
            message=dto.message,
        )
        saved = await self._health_check_repo.save(check)
        return _to_dto(saved)


def _to_dto(check: HealthCheck) -> HealthCheckDTO:
    return HealthCheckDTO(
        id=check.id,
        agent_id=check.agent_id,
        status=check.status,
        checked_at=check.checked_at,
        response_time_ms=check.response_time_ms,
        message=check.message,
    )

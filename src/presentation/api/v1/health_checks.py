from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dtos import RecordHealthCheckDTO
from src.application.use_cases.health_checks import RecordHealthCheckUseCase
from src.domain.exceptions import AgentNotFoundError
from src.presentation.api.dependencies import get_record_health_check_uc
from src.presentation.schemas.health_check_schemas import (
    HealthCheckResponse,
    RecordHealthCheckRequest,
)

router = APIRouter(prefix="/health-checks", tags=["health-checks"])


@router.post("", response_model=HealthCheckResponse, status_code=status.HTTP_201_CREATED)
async def record_health_check(
    body: RecordHealthCheckRequest,
    uc: RecordHealthCheckUseCase = Depends(get_record_health_check_uc),
) -> HealthCheckResponse:
    try:
        dto = RecordHealthCheckDTO(
            agent_id=body.agent_id,
            status=body.status,
            response_time_ms=body.response_time_ms,
            message=body.message,
        )
        result = await uc.execute(dto)
        return HealthCheckResponse(**result.__dict__)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)

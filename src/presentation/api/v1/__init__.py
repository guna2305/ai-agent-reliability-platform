from fastapi import APIRouter

from .agents import router as agents_router
from .agents_v2 import router as agents_v2_router
from .analytics import router as analytics_router
from .api_keys import router as api_keys_router
from .auth import router as auth_router
from .datasets import router as datasets_router
from .evaluations import router as evaluations_router
from .executions import router as executions_router
from .failures import router as failures_router
from .hallucinations import router as hallucinations_router
from .health_checks import router as health_checks_router
from .organizations import router as organizations_router
from .runs import router as runs_router
from .system import router as system_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(system_router)
v1_router.include_router(auth_router)
v1_router.include_router(organizations_router)
v1_router.include_router(agents_v2_router)
v1_router.include_router(api_keys_router)
v1_router.include_router(executions_router)
v1_router.include_router(analytics_router)
v1_router.include_router(datasets_router)
v1_router.include_router(evaluations_router)
v1_router.include_router(hallucinations_router)
v1_router.include_router(failures_router)

# Legacy v1 (kept for backward compat)
v1_router.include_router(agents_router)
v1_router.include_router(runs_router)
v1_router.include_router(health_checks_router)

__all__ = ["v1_router"]

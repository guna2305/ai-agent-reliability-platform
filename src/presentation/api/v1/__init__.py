from fastapi import APIRouter

from .agents import router as agents_router
from .runs import router as runs_router
from .health_checks import router as health_checks_router
from .system import router as system_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(system_router)
v1_router.include_router(agents_router)
v1_router.include_router(runs_router)
v1_router.include_router(health_checks_router)

__all__ = ["v1_router"]

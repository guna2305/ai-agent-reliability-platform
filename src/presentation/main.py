import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.domain.exceptions import DomainException
from src.infrastructure.config.settings import get_settings
from src.infrastructure.observability.logging import configure_logging
from src.presentation.api.v1 import v1_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging(log_level=settings.log_level, use_json=settings.is_production)
    logger.info(
        "Starting platform",
        extra={"env": settings.app_env, "version": settings.app_version},
    )
    yield
    logger.info("Shutting down platform")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AI Agent Evaluation & Reliability Platform",
        description=(
            "Enterprise platform for evaluating, monitoring, debugging, "
            "and improving AI agents in production."
        ),
        version=settings.app_version,
        debug=settings.app_debug,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_tags=[
            {"name": "auth",          "description": "JWT authentication & user management"},
            {"name": "organizations", "description": "Organization & member management"},
            {"name": "agents",        "description": "Agent registry (org-scoped, versioned)"},
            {"name": "api-keys",      "description": "Programmatic API key management"},
            {"name": "system",        "description": "Health check & platform info"},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if settings.is_production else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            excluded_handlers=["/metrics", "/health"],
        ).instrument(app).expose(app, endpoint="/metrics")
    except ImportError:
        pass

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.message, "type": type(exc).__name__},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    app.include_router(v1_router)

    return app


app = create_app()

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    log_level: str = "INFO"
    app_name: str = "AI Agent Evaluation & Reliability Platform"
    app_version: str = "0.1.0"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_reliability"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/agent_reliability"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_echo: bool = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300          # seconds
    redis_rate_limit_window: int = 60   # seconds
    redis_rate_limit_max: int = 1000    # requests per window per org

    # ── Celery ────────────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_always_eager: bool = False  # set True in tests

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = "change-me-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # ── AI Providers ─────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o"
    openai_judge_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-sonnet-4-6"

    # ── Evaluation ───────────────────────────────────────────────────────────
    eval_max_concurrent_jobs: int = 5
    eval_job_timeout_seconds: int = 3600
    hallucination_score_threshold: float = 0.7  # flag above this

    # ── Observability ────────────────────────────────────────────────────────
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "agent-reliability-platform"

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Object Storage ───────────────────────────────────────────────────────
    storage_backend: Literal["local", "azure", "s3"] = "local"
    azure_storage_connection_string: str = ""
    aws_s3_bucket: str = ""

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def database_echo_enabled(self) -> bool:
        return self.database_echo or self.is_development


@lru_cache
def get_settings() -> Settings:
    return Settings()

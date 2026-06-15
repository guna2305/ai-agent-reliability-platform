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
    app_version: str = "0.3.0"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_reliability"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/agent_reliability"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_echo: bool = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300
    redis_rate_limit_window: int = 60
    redis_rate_limit_max: int = 1000

    # ── Celery ────────────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_always_eager: bool = False

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = "change-me-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # ── AI Providers (all optional — Ollama is always the default) ───────────
    # Ollama: free, runs locally, no key required
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"
    default_provider: str = "ollama"
    default_model: str = "llama3.2"

    # OpenAI — optional, only used if key is provided
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o-mini"

    # Anthropic — optional, only used if key is provided
    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-haiku-4-5-20251001"

    # ── Evaluation ───────────────────────────────────────────────────────────
    eval_max_concurrent_jobs: int = 5
    eval_job_timeout_seconds: int = 3600
    hallucination_score_threshold: float = 0.7
    eval_judge_model: str = "llama3.2"  # Ollama model for LLM-as-judge

    # ── Observability ─────────────────────────────────────────────────────────
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "agent-reliability-platform"
    metrics_enabled: bool = False  # Prometheus /metrics (opt-in)

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Object Storage ────────────────────────────────────────────────────────
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
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def anthropic_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

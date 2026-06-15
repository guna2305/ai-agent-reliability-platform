"""Celery tasks for failure clustering (Ollama embeddings, no paid APIs)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.infrastructure.queue.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _cluster_pipeline(org_id: str, k: int | None) -> dict[str, Any]:
    from src.application.use_cases.failures import ClusterFailuresUseCase
    from src.infrastructure.database.connection import get_session_factory
    from src.infrastructure.database.repositories import PostgresFailureReportRepository

    factory = get_session_factory()
    async with factory() as session:
        uc = ClusterFailuresUseCase(PostgresFailureReportRepository(session))
        result = await uc.execute(org_id, k=k)
        await session.commit()
        return {
            "org_id": org_id,
            "status": "completed",
            "clustered": result.clustered,
            "newly_embedded": result.embedded,
            "k": result.k,
        }


@celery_app.task(
    bind=True,
    name="embeddings.cluster_failures",
    queue="analytics",
    max_retries=1,
    default_retry_delay=60,
)
def cluster_failures(self, org_id: str, k: int | None = None) -> dict:
    """Backfill embeddings via Ollama (nomic-embed-text) and re-cluster an org's failures."""
    logger.info("Clustering failures", extra={"org_id": org_id})
    try:
        return asyncio.run(_cluster_pipeline(org_id, k))
    except Exception as exc:
        logger.exception("Clustering task failed", extra={"org_id": org_id})
        raise self.retry(exc=exc)

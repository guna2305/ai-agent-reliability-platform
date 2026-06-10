"""Celery tasks for embedding generation and failure clustering."""
from __future__ import annotations

import logging

from src.infrastructure.queue.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="embeddings.generate_failure_embedding",
    queue="analytics",
)
def generate_failure_embedding(failure_report_id: str) -> dict:
    """Generate embedding vector for a failure report using OpenAI ada-002."""
    logger.info("Generating failure embedding", extra={"failure_report_id": failure_report_id})
    # Phase 6: call OpenAI embeddings API, store vector, trigger re-clustering
    return {"failure_report_id": failure_report_id, "status": "ok"}


@celery_app.task(
    name="embeddings.cluster_failures",
    queue="analytics",
)
def cluster_failures(org_id: str) -> dict:
    """Re-cluster all failure embeddings for an org using k-means."""
    logger.info("Clustering failures", extra={"org_id": org_id})
    return {"org_id": org_id, "status": "ok"}

"""Celery tasks for analytics and cost aggregation."""
from __future__ import annotations

import logging

from src.infrastructure.queue.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="analytics.aggregate_costs",
    queue="analytics",
)
def aggregate_daily_costs(org_id: str, date_str: str) -> dict:
    """Aggregate daily cost metrics per org/agent."""
    logger.info("Aggregating costs", extra={"org_id": org_id, "date": date_str})
    return {"org_id": org_id, "date": date_str, "status": "ok"}


@celery_app.task(
    name="analytics.compute_reliability_metrics",
    queue="analytics",
)
def compute_reliability_metrics(org_id: str, agent_id: str) -> dict:
    """Compute success rate, p50/p95 latency, error rate for an agent."""
    logger.info("Computing reliability metrics", extra={"agent_id": agent_id})
    return {"agent_id": agent_id, "status": "ok"}

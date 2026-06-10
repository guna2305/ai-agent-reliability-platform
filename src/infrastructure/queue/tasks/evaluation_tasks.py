"""Celery tasks for the evaluation pipeline.

These are stubs — full implementation arrives in Phase 4.
The task signatures and queue routing are production-correct.
"""
from __future__ import annotations

import logging

from src.infrastructure.queue.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="evaluations.run_llm_judge",
    queue="evaluations",
    max_retries=2,
    default_retry_delay=30,
)
def run_llm_judge_evaluation(self, eval_run_id: str, config: dict) -> dict:
    """Run LLM-as-a-judge evaluation for an evaluation run."""
    logger.info("Starting LLM judge evaluation", extra={"eval_run_id": eval_run_id})
    # Phase 4: implement evaluation logic
    return {"eval_run_id": eval_run_id, "status": "completed"}


@celery_app.task(
    bind=True,
    name="evaluations.run_ragas",
    queue="evaluations",
    max_retries=2,
    default_retry_delay=30,
)
def run_ragas_evaluation(self, eval_run_id: str, config: dict) -> dict:
    """Run RAGAS evaluation for RAG agents."""
    logger.info("Starting RAGAS evaluation", extra={"eval_run_id": eval_run_id})
    return {"eval_run_id": eval_run_id, "status": "completed"}


@celery_app.task(
    bind=True,
    name="evaluations.detect_hallucinations",
    queue="evaluations",
    max_retries=1,
)
def detect_hallucinations(self, execution_id: str, config: dict) -> dict:
    """Detect hallucinations in an execution output."""
    logger.info("Running hallucination detection", extra={"execution_id": execution_id})
    return {"execution_id": execution_id, "hallucination_score": 0.0}

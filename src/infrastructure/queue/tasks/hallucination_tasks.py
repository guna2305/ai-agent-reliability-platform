"""Celery task for hallucination detection on a completed execution.

Loads the execution, builds a DetectionRequest from its input/output (and any
context captured in metadata), runs the detector ensemble, and persists a
HallucinationReport. Ollama-powered — no paid APIs.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.infrastructure.queue.celery_app import celery_app

logger = logging.getLogger(__name__)


def _extract_text(payload: dict[str, Any] | None, keys: tuple[str, ...]) -> str:
    if not payload:
        return ""
    for key in keys:
        if key in payload and isinstance(payload[key], str):
            return payload[key]
    return str(payload) if payload else ""


async def _run_detection_pipeline(execution_id: str) -> dict[str, Any]:
    from src.application.use_cases.hallucinations import DetectAndSaveUseCase, DetectionRequest
    from src.infrastructure.database.connection import get_session_factory
    from src.infrastructure.database.repositories import (
        PostgresExecutionRepository,
        PostgresHallucinationReportRepository,
    )

    factory = get_session_factory()
    async with factory() as session:
        execution = await PostgresExecutionRepository(session).get_by_id(execution_id)
        if not execution:
            logger.error("Execution not found", extra={"execution_id": execution_id})
            return {"execution_id": execution_id, "status": "not_found"}

        question = _extract_text(execution.input, ("question", "query", "input", "prompt", "text"))
        response = _extract_text(execution.output, ("answer", "output", "response", "text", "content"))
        if not response:
            return {"execution_id": execution_id, "status": "skipped", "reason": "no_output"}

        # Optional grounding material carried on the execution metadata
        reference = execution.metadata.get("reference") if execution.metadata else None
        context_chunks = execution.metadata.get("context_chunks", []) if execution.metadata else []

        uc = DetectAndSaveUseCase(PostgresHallucinationReportRepository(session))
        report = await uc.execute(DetectionRequest(
            execution_id=execution_id,
            question=question,
            response=response,
            reference=reference,
            context_chunks=context_chunks,
        ))
        await session.commit()

        logger.info(
            "Hallucination detection complete",
            extra={
                "execution_id": execution_id,
                "score": float(report.hallucination_score),
                "confidence": float(report.confidence),
                "method": report.detection_method.value,
            },
        )
        return {
            "execution_id": execution_id,
            "status": "completed",
            "report_id": report.id,
            "hallucination_score": float(report.hallucination_score),
            "is_hallucinated": report.is_hallucinated,
        }


@celery_app.task(
    bind=True,
    name="hallucinations.detect",
    queue="evaluations",
    max_retries=2,
    default_retry_delay=30,
)
def detect_hallucinations(self, execution_id: str) -> dict:
    """Detect hallucinations in a completed execution's output."""
    logger.info("Starting hallucination detection", extra={"execution_id": execution_id})
    try:
        return asyncio.run(_run_detection_pipeline(execution_id))
    except Exception as exc:
        logger.exception("Hallucination task failed", extra={"execution_id": execution_id})
        raise self.retry(exc=exc)

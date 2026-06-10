"""Celery tasks for the evaluation pipeline.

Celery workers run in a separate process and are synchronous, so each task
drives an async pipeline via asyncio.run() with its own DB session.

The pipeline:
  1. Load the evaluation run and mark it RUNNING
  2. Load all dataset items
  3. For each item: generate the agent response (via Ollama) and score it
  4. Bulk-save results, aggregate scores, mark the run COMPLETED
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.infrastructure.queue.celery_app import celery_app

logger = logging.getLogger(__name__)


def _extract_question(payload: dict[str, Any]) -> str:
    """Pull human-readable question text from a dataset item's input."""
    for key in ("question", "query", "input", "prompt", "text"):
        if key in payload and isinstance(payload[key], str):
            return payload[key]
    return str(payload)


def _extract_expected(expected: dict[str, Any] | None) -> str | None:
    if not expected:
        return None
    for key in ("answer", "output", "expected", "response", "text"):
        if key in expected and isinstance(expected[key], str):
            return expected[key]
    return str(expected)


async def _run_evaluation_pipeline(eval_run_id: str) -> dict[str, Any]:
    from src.infrastructure.database.connection import get_session_factory
    from src.infrastructure.database.repositories import (
        PostgresEvaluationRunRepository,
        PostgresEvaluationResultRepository,
        PostgresDatasetItemRepository,
    )
    from src.application.use_cases.evaluations import (
        ScoringInput, ScoringConfig, score_item, aggregate_results,
    )
    from src.infrastructure.ai.providers import call_llm

    factory = get_session_factory()
    async with factory() as session:
        run_repo = PostgresEvaluationRunRepository(session)
        result_repo = PostgresEvaluationResultRepository(session)
        item_repo = PostgresDatasetItemRepository(session)

        run = await run_repo.get_by_id(eval_run_id)
        if not run:
            logger.error("Eval run not found", extra={"eval_run_id": eval_run_id})
            return {"eval_run_id": eval_run_id, "status": "not_found"}

        if not run.dataset_id:
            run.fail()
            await run_repo.update(run)
            await session.commit()
            return {"eval_run_id": eval_run_id, "status": "failed", "reason": "no_dataset"}

        items = await item_repo.list_by_dataset(run.dataset_id, limit=10_000, offset=0)
        run.start(total_items=len(items))
        await run_repo.update(run)
        await session.commit()

        config = ScoringConfig(
            eval_type=run.eval_type,
            pass_threshold=run.config.get("pass_threshold", 0.6),
            judge_model=run.config.get("judge_model"),
            use_semantic=run.config.get("use_semantic", True),
        )

        results = []
        for item in items:
            question = _extract_question(item.input)
            expected = _extract_expected(item.expected_output)
            try:
                # Generate the agent response via Ollama (free, local)
                llm = await call_llm(prompt=question)
                response_text = llm.content
            except Exception as e:
                logger.warning(
                    "Response generation failed; scoring empty response",
                    extra={"error": str(e), "item_id": item.id},
                )
                response_text = ""
                run.record_item_failed()

            scoring_input = ScoringInput(
                dataset_item_id=item.id,
                execution_id=None,
                question=question,
                response=response_text,
                expected_output=expected,
                context_chunks=item.context,
            )
            try:
                result = await score_item(eval_run_id, scoring_input, config)
                results.append(result)
                run.record_item_completed()
            except Exception as e:
                logger.warning("Scoring failed for item", extra={"error": str(e), "item_id": item.id})
                run.record_item_failed()

        await result_repo.save_bulk(results)
        aggregates = aggregate_results(results)
        run.complete(aggregate_scores=aggregates)
        await run_repo.update(run)
        await session.commit()

        logger.info(
            "Evaluation completed",
            extra={"eval_run_id": eval_run_id, "scored": len(results), **aggregates},
        )
        return {"eval_run_id": eval_run_id, "status": "completed", "aggregates": aggregates}


@celery_app.task(
    bind=True,
    name="evaluations.run_evaluation",
    queue="evaluations",
    max_retries=2,
    default_retry_delay=30,
)
def run_evaluation(self, eval_run_id: str) -> dict:
    """Run a full evaluation (LLM-judge / ground-truth / RAG) for an evaluation run."""
    logger.info("Starting evaluation", extra={"eval_run_id": eval_run_id})
    try:
        return asyncio.run(_run_evaluation_pipeline(eval_run_id))
    except Exception as exc:
        logger.exception("Evaluation task failed", extra={"eval_run_id": eval_run_id})
        raise self.retry(exc=exc)

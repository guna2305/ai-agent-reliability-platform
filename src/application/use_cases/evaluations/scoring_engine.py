"""Scoring engine — orchestrates evaluators over dataset items.

This is the core evaluation logic, kept independent of the DB so it can be
unit-tested with fakes. The Celery task wires repositories around it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.domain.entities import EvaluationResult
from src.domain.value_objects import EvaluationType


@dataclass
class ScoringInput:
    """One item to score: the question, the agent's response, and references."""
    dataset_item_id: str | None
    execution_id: str | None
    question: str
    response: str
    expected_output: str | None = None
    context_chunks: list[str] = field(default_factory=list)


@dataclass
class ScoringConfig:
    eval_type: EvaluationType
    pass_threshold: float = 0.6
    judge_model: str | None = None
    use_semantic: bool = True


async def score_item(
    eval_run_id: str,
    item: ScoringInput,
    config: ScoringConfig,
) -> EvaluationResult:
    """Score a single item according to the eval_type, returning a result entity."""
    scores: dict[str, float] = {}
    reasoning_parts: list[str] = []

    if config.eval_type == EvaluationType.LLM_JUDGE:
        from src.infrastructure.ai.evaluators.llm_judge import run_full_judge
        context = "\n\n".join(item.context_chunks) if item.context_chunks else None
        judge = await run_full_judge(
            question=item.question,
            response=item.response,
            expected=item.expected_output,
            context=context,
            model=config.judge_model,
        )
        for metric, js in judge.items():
            scores[metric] = js.score
            reasoning_parts.append(f"{metric}={js.score}: {js.reasoning}")

    elif config.eval_type == EvaluationType.GROUND_TRUTH:
        from src.infrastructure.ai.evaluators.ground_truth import evaluate_ground_truth
        if item.expected_output:
            gt = await evaluate_ground_truth(
                expected=item.expected_output,
                actual=item.response,
                use_semantic=config.use_semantic,
            )
            scores["correctness"] = gt.overall
            reasoning_parts.append(gt.reasoning)

    elif config.eval_type == EvaluationType.RAG:
        from src.infrastructure.ai.evaluators.rag_evaluator import evaluate_rag
        rag = await evaluate_rag(
            question=item.question,
            response=item.response,
            context_chunks=item.context_chunks,
            expected=item.expected_output,
            model=config.judge_model,
        )
        if rag.context_precision is not None:
            scores["context_precision"] = rag.context_precision
        if rag.context_recall is not None:
            scores["context_recall"] = rag.context_recall
        if rag.faithfulness is not None:
            scores["faithfulness"] = rag.faithfulness
        if rag.answer_relevancy is not None:
            scores["answer_relevancy"] = rag.answer_relevancy
        reasoning_parts.append("RAG metrics computed via Ollama")

    # Overall pass/fail: mean of available scores vs threshold
    overall = sum(scores.values()) / len(scores) if scores else 0.0
    passed = overall >= config.pass_threshold

    return EvaluationResult.create(
        eval_run_id=eval_run_id,
        passed=passed,
        execution_id=item.execution_id,
        dataset_item_id=item.dataset_item_id,
        correctness_score=scores.get("correctness"),
        relevance_score=scores.get("relevance"),
        faithfulness_score=scores.get("faithfulness"),
        helpfulness_score=scores.get("helpfulness"),
        context_precision=scores.get("context_precision"),
        context_recall=scores.get("context_recall"),
        answer_relevancy=scores.get("answer_relevancy"),
        reasoning=" | ".join(reasoning_parts) if reasoning_parts else None,
    )


def aggregate_results(results: list[EvaluationResult]) -> dict[str, Any]:
    """Compute mean per-metric scores and pass rate across results."""
    if not results:
        return {"total": 0, "passed": 0, "pass_rate": 0.0}

    metric_fields = [
        "correctness_score", "relevance_score", "faithfulness_score",
        "helpfulness_score", "context_precision", "context_recall", "answer_relevancy",
    ]
    aggregates: dict[str, Any] = {}
    for field_name in metric_fields:
        values = [
            float(getattr(r, field_name))
            for r in results
            if getattr(r, field_name) is not None
        ]
        if values:
            key = field_name.replace("_score", "")
            aggregates[key] = round(sum(values) / len(values), 4)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    aggregates["total"] = total
    aggregates["passed"] = passed
    aggregates["pass_rate"] = round(passed / total, 4) if total else 0.0
    return aggregates

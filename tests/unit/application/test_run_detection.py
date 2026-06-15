"""Unit tests for run_detection orchestration (detectors monkeypatched)."""
import pytest

import src.infrastructure.ai.hallucination as halluc
from src.application.use_cases.hallucinations import DetectionRequest, run_detection
from src.domain.value_objects import DetectionMethod


def _signal(method, score, conf, segments=None):
    return halluc.HallucinationSignal(
        method=method, score=score, confidence=conf, flagged_segments=segments or [],
    )


@pytest.mark.asyncio
async def test_run_detection_llm_only(monkeypatch):
    async def fake_judge(question, response, model=None):
        return _signal(DetectionMethod.LLM_JUDGE, 0.4, 0.8)

    monkeypatch.setattr(halluc, "detect_llm_judge", fake_judge)

    report = await run_detection(DetectionRequest(
        execution_id="exec-1",
        question="What is the capital of France?",
        response="The capital is Paris.",
    ))
    assert report.execution_id == "exec-1"
    assert float(report.hallucination_score) == 0.4
    assert report.detection_method == DetectionMethod.LLM_JUDGE
    assert report.is_hallucinated is False


@pytest.mark.asyncio
async def test_run_detection_with_reference_and_context(monkeypatch):
    async def fake_judge(question, response, model=None):
        return _signal(DetectionMethod.LLM_JUDGE, 0.8, 1.0, [{"text": "x", "reason": "y"}])

    async def fake_ref(response, reference, model=None):
        return _signal(DetectionMethod.REFERENCE_BASED, 0.9, 1.0)

    async def fake_ctx(response, context_chunks, model=None):
        return _signal(DetectionMethod.RETRIEVAL_CONSISTENCY, 0.7, 0.5)

    monkeypatch.setattr(halluc, "detect_llm_judge", fake_judge)
    monkeypatch.setattr(halluc, "detect_reference_based", fake_ref)
    monkeypatch.setattr(halluc, "detect_retrieval_consistency", fake_ctx)

    report = await run_detection(DetectionRequest(
        execution_id="exec-2",
        question="Q",
        response="R",
        reference="known good answer",
        context_chunks=["chunk one", "chunk two"],
    ))
    # All three detectors ran and fused into a high score
    assert float(report.hallucination_score) > 0.7
    assert report.is_hallucinated is True
    assert len(report.flagged_segments) >= 1


@pytest.mark.asyncio
async def test_run_detection_all_detectors_unavailable(monkeypatch):
    async def dead(*args, **kwargs):
        return _signal(DetectionMethod.LLM_JUDGE, 0.0, 0.0)

    monkeypatch.setattr(halluc, "detect_llm_judge", dead)

    report = await run_detection(DetectionRequest(
        execution_id="exec-3", question="Q", response="R",
    ))
    # No usable signal -> zero confidence, not flagged
    assert float(report.confidence) == 0.0
    assert report.is_hallucinated is False

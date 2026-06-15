"""Unit tests for the HallucinationReport entity."""
from decimal import Decimal

from src.domain.entities import HallucinationReport
from src.domain.value_objects import DetectionMethod


def test_create_defaults():
    r = HallucinationReport.create(
        execution_id="exec-1",
        hallucination_score=0.3,
        confidence=0.8,
        detection_method=DetectionMethod.LLM_JUDGE,
    )
    assert r.is_confirmed is False
    assert r.hallucination_score == Decimal("0.3")
    assert r.confidence == Decimal("0.8")
    assert r.flagged_segments == []
    assert r.id is not None


def test_is_hallucinated_threshold():
    low = HallucinationReport.create(
        execution_id="e", hallucination_score=0.69, confidence=0.9,
        detection_method=DetectionMethod.LLM_JUDGE,
    )
    high = HallucinationReport.create(
        execution_id="e", hallucination_score=0.7, confidence=0.9,
        detection_method=DetectionMethod.LLM_JUDGE,
    )
    assert low.is_hallucinated is False
    assert high.is_hallucinated is True


def test_confirm():
    r = HallucinationReport.create(
        execution_id="e", hallucination_score=0.9, confidence=0.95,
        detection_method=DetectionMethod.REFERENCE_BASED,
    )
    assert r.is_confirmed is False
    r.confirm()
    assert r.is_confirmed is True


def test_flagged_segments_preserved():
    segs = [{"text": "The moon is made of cheese", "reason": "fabricated"}]
    r = HallucinationReport.create(
        execution_id="e", hallucination_score=0.95, confidence=0.9,
        detection_method=DetectionMethod.RETRIEVAL_CONSISTENCY,
        flagged_segments=segs,
    )
    assert r.flagged_segments == segs

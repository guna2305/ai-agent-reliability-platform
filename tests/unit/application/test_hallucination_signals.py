"""Unit tests for hallucination signal fusion (pure, no Ollama)."""
from src.domain.value_objects import DetectionMethod
from src.infrastructure.ai.hallucination import HallucinationSignal, combine_signals


def _sig(method, score, conf, segments=None):
    return HallucinationSignal(
        method=method, score=score, confidence=conf,
        flagged_segments=segments or [],
    )


def test_combine_empty_returns_zero_confidence():
    fused = combine_signals([])
    assert fused.score == 0.0
    assert fused.confidence == 0.0


def test_combine_skips_zero_confidence_detectors():
    # A dead detector (confidence 0) must not drag the score toward 0
    signals = [
        _sig(DetectionMethod.LLM_JUDGE, score=0.9, conf=1.0),
        _sig(DetectionMethod.REFERENCE_BASED, score=0.0, conf=0.0),  # unavailable
    ]
    fused = combine_signals(signals)
    assert fused.score == 0.9
    assert fused.confidence == 1.0


def test_combine_confidence_weighted_average():
    signals = [
        _sig(DetectionMethod.LLM_JUDGE, score=0.8, conf=1.0),
        _sig(DetectionMethod.RETRIEVAL_CONSISTENCY, score=0.2, conf=0.5),
    ]
    fused = combine_signals(signals)
    # weighted = (0.8*1.0 + 0.2*0.5) / 1.5 = 0.6 ; mean_conf = 1.5/2 = 0.75
    assert fused.score == 0.6
    assert fused.confidence == 0.75


def test_combine_dominant_method_is_highest_confidence():
    signals = [
        _sig(DetectionMethod.LLM_JUDGE, score=0.5, conf=0.4),
        _sig(DetectionMethod.REFERENCE_BASED, score=0.5, conf=0.9),
    ]
    fused = combine_signals(signals)
    assert fused.method == DetectionMethod.REFERENCE_BASED


def test_combine_concatenates_flagged_segments():
    signals = [
        _sig(DetectionMethod.LLM_JUDGE, 0.6, 0.8, [{"text": "a", "reason": "x"}]),
        _sig(DetectionMethod.REFERENCE_BASED, 0.7, 0.9, [{"text": "b", "reason": "y"}]),
    ]
    fused = combine_signals(signals)
    assert len(fused.flagged_segments) == 2


def test_combine_all_dead_detectors():
    signals = [
        _sig(DetectionMethod.LLM_JUDGE, 0.0, 0.0),
        _sig(DetectionMethod.REFERENCE_BASED, 0.0, 0.0),
    ]
    fused = combine_signals(signals)
    assert fused.confidence == 0.0

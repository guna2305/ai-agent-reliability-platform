"""Rule-based failure classification.

Inspects an execution's signals (status, error text, tool calls, token/cost
usage, hallucination score) and classifies the dominant failure into a
FailureType + FailureSeverity with a human-readable title/description.

Deterministic and dependency-free so it's fast and fully unit-testable. The
embedding + clustering step (Ollama) groups these reports afterward.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.domain.value_objects import ExecutionStatus, FailureSeverity, FailureType


@dataclass
class FailureClassification:
    failure_type: FailureType
    severity: FailureSeverity
    title: str
    description: str
    root_cause: str | None = None


@dataclass
class FailureSignals:
    """Normalized inputs the classifier reasons over."""
    status: ExecutionStatus
    error_message: str | None = None
    tool_call_errors: list[str] = field(default_factory=list)
    empty_output: bool = False
    hallucination_score: float | None = None
    total_cost_usd: Decimal | None = None
    duration_ms: int | None = None
    cost_threshold_usd: float = 1.0
    latency_threshold_ms: int = 30_000


_ERROR_KEYWORDS: dict[str, FailureType] = {
    "timeout": FailureType.TIMEOUT,
    "timed out": FailureType.TIMEOUT,
    "deadline": FailureType.TIMEOUT,
    "retrieval": FailureType.RETRIEVAL,
    "no documents": FailureType.RETRIEVAL,
    "empty context": FailureType.RETRIEVAL,
    "tool": FailureType.TOOL,
    "function call": FailureType.TOOL,
    "json": FailureType.OUTPUT,
    "parse": FailureType.OUTPUT,
    "schema": FailureType.OUTPUT,
    "validation": FailureType.OUTPUT,
    "prompt": FailureType.PROMPT,
    "token limit": FailureType.PROMPT,
    "context length": FailureType.PROMPT,
}


def _match_error_type(error: str) -> FailureType | None:
    low = error.lower()
    for keyword, ftype in _ERROR_KEYWORDS.items():
        if keyword in low:
            return ftype
    return None


def classify_failure(signals: FailureSignals) -> FailureClassification | None:
    """Return a classification, or None when the execution is not a failure."""

    # 1. Hallucination takes priority — it's a silent failure even on "success"
    if signals.hallucination_score is not None and signals.hallucination_score >= 0.7:
        return FailureClassification(
            failure_type=FailureType.HALLUCINATION,
            severity=FailureSeverity.HIGH,
            title="Hallucinated output detected",
            description=(
                f"Output flagged with hallucination score "
                f"{signals.hallucination_score:.2f} (threshold 0.70)."
            ),
            root_cause="Model produced unsupported or fabricated content.",
        )

    # 2. Timeout
    if signals.status == ExecutionStatus.TIMED_OUT:
        return FailureClassification(
            failure_type=FailureType.TIMEOUT,
            severity=FailureSeverity.HIGH,
            title="Execution timed out",
            description=f"Execution exceeded the time limit "
                        f"({signals.duration_ms or 0} ms elapsed).",
            root_cause="Agent did not complete within the allotted time.",
        )

    # 3. Explicit failure with an error message — classify by keyword
    if signals.status == ExecutionStatus.FAILED and signals.error_message:
        matched = _match_error_type(signals.error_message)
        ftype = matched or FailureType.UNKNOWN
        return FailureClassification(
            failure_type=ftype,
            severity=FailureSeverity.HIGH if matched else FailureSeverity.MEDIUM,
            title=f"{ftype.value.capitalize()} failure",
            description=signals.error_message[:480],
            root_cause=None,
        )

    # 4. Tool misuse — tool calls errored even if the run technically finished
    if signals.tool_call_errors:
        return FailureClassification(
            failure_type=FailureType.TOOL,
            severity=FailureSeverity.MEDIUM,
            title="Tool call failure",
            description="; ".join(signals.tool_call_errors)[:480],
            root_cause="One or more tool invocations failed.",
        )

    # 5. Empty / invalid output on an otherwise-successful run
    if signals.empty_output:
        return FailureClassification(
            failure_type=FailureType.OUTPUT,
            severity=FailureSeverity.MEDIUM,
            title="Empty or invalid output",
            description="Execution completed but produced no usable output.",
            root_cause="Agent returned an empty response.",
        )

    # 6. Cost overrun
    if (
        signals.total_cost_usd is not None
        and float(signals.total_cost_usd) > signals.cost_threshold_usd
    ):
        return FailureClassification(
            failure_type=FailureType.COST,
            severity=FailureSeverity.LOW,
            title="Cost threshold exceeded",
            description=f"Execution cost ${float(signals.total_cost_usd):.4f} "
                        f"exceeded the ${signals.cost_threshold_usd:.2f} threshold.",
            root_cause="Excessive token usage.",
        )

    # 7. Generic failed status with no detail
    if signals.status == ExecutionStatus.FAILED:
        return FailureClassification(
            failure_type=FailureType.UNKNOWN,
            severity=FailureSeverity.MEDIUM,
            title="Execution failed",
            description="Execution failed without a specific error message.",
        )

    return None

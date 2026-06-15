"""Hallucination detection orchestration.

run_detection() is DB-independent (testable with fakes): it runs the chosen
detectors, fuses their signals, and returns a HallucinationReport entity.
The DB-backed use cases persist / query reports.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.application.interfaces.repositories import HallucinationReportRepository
from src.domain.entities import HallucinationReport
from src.domain.exceptions import DomainException
from src.domain.value_objects import DetectionMethod


class HallucinationReportNotFoundError(DomainException):
    def __init__(self, report_id: str) -> None:
        super().__init__(f"Hallucination report '{report_id}' not found")


@dataclass(frozen=True)
class DetectionRequest:
    execution_id: str
    question: str
    response: str
    reference: str | None = None
    context_chunks: list[str] = field(default_factory=list)
    eval_result_id: str | None = None
    judge_model: str | None = None


async def run_detection(req: DetectionRequest) -> HallucinationReport:
    """Run all applicable detectors, fuse signals, return a (transient) report."""
    from src.infrastructure.ai.hallucination import (
        HallucinationSignal,
        combine_signals,
        detect_llm_judge,
        detect_reference_based,
        detect_retrieval_consistency,
    )

    signals: list[HallucinationSignal] = []

    # LLM self-judge always runs (needs only question + response)
    signals.append(await detect_llm_judge(req.question, req.response, req.judge_model))

    if req.reference:
        signals.append(
            await detect_reference_based(req.response, req.reference, req.judge_model)
        )
    if req.context_chunks:
        signals.append(
            await detect_retrieval_consistency(req.response, req.context_chunks, req.judge_model)
        )

    fused = combine_signals(signals)

    return HallucinationReport.create(
        execution_id=req.execution_id,
        hallucination_score=fused.score,
        confidence=fused.confidence,
        detection_method=fused.method,
        flagged_segments=fused.flagged_segments,
        reasoning=fused.reasoning,
        eval_result_id=req.eval_result_id,
    )


class DetectAndSaveUseCase:
    def __init__(self, repo: HallucinationReportRepository) -> None:
        self._repo = repo

    async def execute(self, req: DetectionRequest) -> HallucinationReport:
        report = await run_detection(req)
        return await self._repo.save(report)


class ListHallucinationsByExecutionUseCase:
    def __init__(self, repo: HallucinationReportRepository) -> None:
        self._repo = repo

    async def execute(self, execution_id: str) -> list[HallucinationReport]:
        return await self._repo.list_by_execution(execution_id)


class ListFlaggedHallucinationsUseCase:
    def __init__(self, repo: HallucinationReportRepository) -> None:
        self._repo = repo

    async def execute(
        self, org_id: str, min_score: float = 0.7, limit: int = 50, offset: int = 0
    ) -> tuple[list[HallucinationReport], int]:
        reports = await self._repo.list_flagged_by_org(org_id, min_score, limit, offset)
        total = await self._repo.count_flagged_by_org(org_id, min_score)
        return reports, total


class ConfirmHallucinationUseCase:
    def __init__(self, repo: HallucinationReportRepository) -> None:
        self._repo = repo

    async def execute(self, report_id: str) -> HallucinationReport:
        report = await self._repo.get_by_id(report_id)
        if not report:
            raise HallucinationReportNotFoundError(report_id)
        report.confirm()
        return await self._repo.update(report)

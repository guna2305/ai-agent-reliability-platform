from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from src.domain.value_objects import EvaluationStatus, EvaluationType, FailureType, FailureSeverity, DetectionMethod


@dataclass
class EvaluationRun:
    id: str
    org_id: str
    agent_id: str
    agent_version_id: str | None
    dataset_id: str | None
    name: str
    description: str | None
    status: EvaluationStatus
    eval_type: EvaluationType
    config: dict[str, Any]
    total_items: int
    completed_items: int
    failed_items: int
    aggregate_scores: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_by: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        org_id: str,
        agent_id: str,
        created_by: str,
        name: str,
        eval_type: EvaluationType,
        agent_version_id: str | None = None,
        dataset_id: str | None = None,
        description: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> EvaluationRun:
        return cls(
            id=str(uuid.uuid4()),
            org_id=org_id,
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            dataset_id=dataset_id,
            name=name,
            description=description,
            status=EvaluationStatus.PENDING,
            eval_type=eval_type,
            config=config or {},
            total_items=0,
            completed_items=0,
            failed_items=0,
            aggregate_scores={},
            started_at=None,
            completed_at=None,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )

    def start(self, total_items: int) -> None:
        self.status = EvaluationStatus.RUNNING
        self.total_items = total_items
        self.started_at = datetime.now(timezone.utc)

    def record_item_completed(self) -> None:
        self.completed_items += 1

    def record_item_failed(self) -> None:
        self.failed_items += 1

    def complete(self, aggregate_scores: dict[str, Any]) -> None:
        self.status = EvaluationStatus.COMPLETED
        self.aggregate_scores = aggregate_scores
        self.completed_at = datetime.now(timezone.utc)

    def fail(self) -> None:
        self.status = EvaluationStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)

    @property
    def pass_rate(self) -> float:
        if self.total_items == 0:
            return 0.0
        return self.completed_items / self.total_items


@dataclass
class EvaluationResult:
    id: str
    eval_run_id: str
    execution_id: str | None
    dataset_item_id: str | None
    correctness_score: Decimal | None
    relevance_score: Decimal | None
    faithfulness_score: Decimal | None
    helpfulness_score: Decimal | None
    hallucination_score: Decimal | None
    context_precision: Decimal | None
    context_recall: Decimal | None
    answer_relevancy: Decimal | None
    custom_scores: dict[str, Any]
    reasoning: str | None
    passed: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        eval_run_id: str,
        passed: bool,
        execution_id: str | None = None,
        dataset_item_id: str | None = None,
        correctness_score: float | None = None,
        relevance_score: float | None = None,
        faithfulness_score: float | None = None,
        helpfulness_score: float | None = None,
        hallucination_score: float | None = None,
        context_precision: float | None = None,
        context_recall: float | None = None,
        answer_relevancy: float | None = None,
        custom_scores: dict[str, Any] | None = None,
        reasoning: str | None = None,
    ) -> EvaluationResult:
        def _dec(v: float | None) -> Decimal | None:
            return Decimal(str(v)) if v is not None else None

        return cls(
            id=str(uuid.uuid4()),
            eval_run_id=eval_run_id,
            execution_id=execution_id,
            dataset_item_id=dataset_item_id,
            correctness_score=_dec(correctness_score),
            relevance_score=_dec(relevance_score),
            faithfulness_score=_dec(faithfulness_score),
            helpfulness_score=_dec(helpfulness_score),
            hallucination_score=_dec(hallucination_score),
            context_precision=_dec(context_precision),
            context_recall=_dec(context_recall),
            answer_relevancy=_dec(answer_relevancy),
            custom_scores=custom_scores or {},
            reasoning=reasoning,
            passed=passed,
            created_at=datetime.now(timezone.utc),
        )


@dataclass
class HallucinationReport:
    id: str
    execution_id: str
    eval_result_id: str | None
    hallucination_score: Decimal
    confidence: Decimal
    detection_method: DetectionMethod
    flagged_segments: list[dict[str, Any]]
    reasoning: str | None
    is_confirmed: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        execution_id: str,
        hallucination_score: float,
        confidence: float,
        detection_method: DetectionMethod,
        flagged_segments: list[dict[str, Any]] | None = None,
        reasoning: str | None = None,
        eval_result_id: str | None = None,
    ) -> HallucinationReport:
        return cls(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            eval_result_id=eval_result_id,
            hallucination_score=Decimal(str(hallucination_score)),
            confidence=Decimal(str(confidence)),
            detection_method=detection_method,
            flagged_segments=flagged_segments or [],
            reasoning=reasoning,
            is_confirmed=False,
            created_at=datetime.now(timezone.utc),
        )


@dataclass
class FailureReport:
    id: str
    org_id: str
    execution_id: str
    eval_result_id: str | None
    failure_type: FailureType
    severity: FailureSeverity
    title: str
    description: str
    root_cause: str | None
    embedding_vector: list[float] | None
    cluster_id: int | None
    is_resolved: bool
    resolution_notes: str | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        org_id: str,
        execution_id: str,
        failure_type: FailureType,
        severity: FailureSeverity,
        title: str,
        description: str,
        root_cause: str | None = None,
        eval_result_id: str | None = None,
    ) -> FailureReport:
        return cls(
            id=str(uuid.uuid4()),
            org_id=org_id,
            execution_id=execution_id,
            eval_result_id=eval_result_id,
            failure_type=failure_type,
            severity=severity,
            title=title,
            description=description,
            root_cause=root_cause,
            embedding_vector=None,
            cluster_id=None,
            is_resolved=False,
            resolution_notes=None,
            created_at=datetime.now(timezone.utc),
        )

    def set_embedding(self, vector: list[float]) -> None:
        self.embedding_vector = vector

    def assign_cluster(self, cluster_id: int) -> None:
        self.cluster_id = cluster_id

    def resolve(self, notes: str) -> None:
        self.is_resolved = True
        self.resolution_notes = notes

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.connection import Base


class DatasetModel(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_type: Mapped[str] = mapped_column(String(30), nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    items: Mapped[list[DatasetItemModel]] = relationship(
        "DatasetItemModel", back_populates="dataset", cascade="all, delete-orphan", lazy="noload"
    )


class DatasetItemModel(Base):
    __tablename__ = "dataset_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    input_: Mapped[dict] = mapped_column("input", JSONB, nullable=False)
    expected_output_: Mapped[dict | None] = mapped_column("expected_output", JSONB, nullable=True)
    context: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    dataset: Mapped[DatasetModel] = relationship(
        "DatasetModel", back_populates="items", lazy="noload"
    )


class EvaluationRunModel(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    eval_type: Mapped[str] = mapped_column(String(30), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    total_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aggregate_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    results: Mapped[list[EvaluationResultModel]] = relationship(
        "EvaluationResultModel", back_populates="eval_run", cascade="all, delete-orphan", lazy="noload"
    )


class EvaluationResultModel(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    eval_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dataset_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    correctness_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    relevance_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    faithfulness_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    helpfulness_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    hallucination_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    context_precision: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    context_recall: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    answer_relevancy: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    custom_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    eval_run: Mapped[EvaluationRunModel] = relationship(
        "EvaluationRunModel", back_populates="results", lazy="noload"
    )


class HallucinationReportModel(Base):
    __tablename__ = "hallucination_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    eval_result_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    hallucination_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    detection_method: Mapped[str] = mapped_column(String(50), nullable=False)
    flagged_segments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FailureReportModel(Base):
    __tablename__ = "failure_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    execution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    eval_result_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    failure_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    # embedding_vector stored as text JSON for portability; use pgvector in prod
    embedding_vector: Mapped[str | None] = mapped_column(Text, nullable=True)
    cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

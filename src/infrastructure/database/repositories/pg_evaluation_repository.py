from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.repositories.evaluation_repository import (
    DatasetItemRepository,
    DatasetRepository,
    EvaluationResultRepository,
    EvaluationRunRepository,
)
from src.domain.entities import Dataset, DatasetItem, EvaluationResult, EvaluationRun
from src.domain.value_objects import EvaluationStatus, EvaluationType
from src.infrastructure.database.models.evaluation_model import (
    DatasetItemModel,
    DatasetModel,
    EvaluationResultModel,
    EvaluationRunModel,
)


class PostgresDatasetRepository(DatasetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, dataset: Dataset) -> Dataset:
        self._session.add(_ds_to_model(dataset))
        await self._session.flush()
        return dataset

    async def get_by_id(self, dataset_id: str) -> Dataset | None:
        row = await self._session.get(DatasetModel, dataset_id)
        return _model_to_ds(row) if row else None

    async def list_by_org(self, org_id: str, limit: int = 50, offset: int = 0) -> list[Dataset]:
        stmt = (
            select(DatasetModel)
            .where(DatasetModel.org_id == org_id)
            .order_by(DatasetModel.created_at.desc())
            .limit(limit).offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_model_to_ds(r) for r in result.scalars().all()]

    async def count_by_org(self, org_id: str) -> int:
        stmt = select(func.count()).select_from(DatasetModel).where(DatasetModel.org_id == org_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete(self, dataset_id: str, org_id: str) -> bool:
        stmt = select(DatasetModel).where(
            DatasetModel.id == dataset_id, DatasetModel.org_id == org_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


class PostgresDatasetItemRepository(DatasetItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, item: DatasetItem) -> DatasetItem:
        self._session.add(_item_to_model(item))
        await self._session.flush()
        return item

    async def save_bulk(self, items: list[DatasetItem]) -> list[DatasetItem]:
        for item in items:
            self._session.add(_item_to_model(item))
        await self._session.flush()
        return items

    async def get_by_id(self, item_id: str) -> DatasetItem | None:
        row = await self._session.get(DatasetItemModel, item_id)
        return _model_to_item(row) if row else None

    async def list_by_dataset(
        self, dataset_id: str, limit: int = 100, offset: int = 0
    ) -> list[DatasetItem]:
        stmt = (
            select(DatasetItemModel)
            .where(DatasetItemModel.dataset_id == dataset_id)
            .order_by(DatasetItemModel.created_at)
            .limit(limit).offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_model_to_item(r) for r in result.scalars().all()]

    async def count_by_dataset(self, dataset_id: str) -> int:
        stmt = select(func.count()).select_from(DatasetItemModel).where(
            DatasetItemModel.dataset_id == dataset_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()


class PostgresEvaluationRunRepository(EvaluationRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, run: EvaluationRun) -> EvaluationRun:
        self._session.add(_run_to_model(run))
        await self._session.flush()
        return run

    async def get_by_id(self, run_id: str) -> EvaluationRun | None:
        row = await self._session.get(EvaluationRunModel, run_id)
        return _model_to_run(row) if row else None

    async def update(self, run: EvaluationRun) -> EvaluationRun:
        row = await self._session.get(EvaluationRunModel, run.id)
        if row:
            row.status = run.status.value
            row.total_items = run.total_items
            row.completed_items = run.completed_items
            row.failed_items = run.failed_items
            row.aggregate_scores = run.aggregate_scores
            row.started_at = run.started_at
            row.completed_at = run.completed_at
            await self._session.flush()
        return run

    async def list_by_org(
        self,
        org_id: str,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EvaluationRun]:
        stmt = (
            select(EvaluationRunModel)
            .where(EvaluationRunModel.org_id == org_id)
            .order_by(EvaluationRunModel.created_at.desc())
        )
        if agent_id:
            stmt = stmt.where(EvaluationRunModel.agent_id == agent_id)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_model_to_run(r) for r in result.scalars().all()]

    async def count_by_org(self, org_id: str, agent_id: str | None = None) -> int:
        stmt = select(func.count()).select_from(EvaluationRunModel).where(
            EvaluationRunModel.org_id == org_id
        )
        if agent_id:
            stmt = stmt.where(EvaluationRunModel.agent_id == agent_id)
        result = await self._session.execute(stmt)
        return result.scalar_one()


class PostgresEvaluationResultRepository(EvaluationResultRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, result: EvaluationResult) -> EvaluationResult:
        self._session.add(_result_to_model(result))
        await self._session.flush()
        return result

    async def save_bulk(self, results: list[EvaluationResult]) -> None:
        for r in results:
            self._session.add(_result_to_model(r))
        await self._session.flush()

    async def list_by_run(
        self, run_id: str, passed: bool | None = None, limit: int = 100, offset: int = 0
    ) -> list[EvaluationResult]:
        stmt = (
            select(EvaluationResultModel)
            .where(EvaluationResultModel.eval_run_id == run_id)
            .order_by(EvaluationResultModel.created_at)
            .limit(limit).offset(offset)
        )
        if passed is not None:
            stmt = stmt.where(EvaluationResultModel.passed == passed)
        result = await self._session.execute(stmt)
        return [_model_to_result(r) for r in result.scalars().all()]

    async def count_by_run(self, run_id: str, passed: bool | None = None) -> int:
        stmt = select(func.count()).select_from(EvaluationResultModel).where(
            EvaluationResultModel.eval_run_id == run_id
        )
        if passed is not None:
            stmt = stmt.where(EvaluationResultModel.passed == passed)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_aggregate_scores(self, run_id: str) -> dict:
        stmt = select(
            func.avg(EvaluationResultModel.correctness_score).label("correctness"),
            func.avg(EvaluationResultModel.relevance_score).label("relevance"),
            func.avg(EvaluationResultModel.faithfulness_score).label("faithfulness"),
            func.avg(EvaluationResultModel.helpfulness_score).label("helpfulness"),
            func.avg(EvaluationResultModel.hallucination_score).label("hallucination"),
            func.avg(EvaluationResultModel.context_precision).label("context_precision"),
            func.avg(EvaluationResultModel.context_recall).label("context_recall"),
            func.avg(EvaluationResultModel.answer_relevancy).label("answer_relevancy"),
            func.count().label("total"),
            func.count().filter(EvaluationResultModel.passed.is_(True)).label("passed"),
        ).where(EvaluationResultModel.eval_run_id == run_id)
        result = await self._session.execute(stmt)
        row = result.one()

        def _f(v) -> float | None:
            return round(float(v), 4) if v is not None else None

        total = row.total or 0
        return {
            "correctness": _f(row.correctness),
            "relevance": _f(row.relevance),
            "faithfulness": _f(row.faithfulness),
            "helpfulness": _f(row.helpfulness),
            "hallucination": _f(row.hallucination),
            "context_precision": _f(row.context_precision),
            "context_recall": _f(row.context_recall),
            "answer_relevancy": _f(row.answer_relevancy),
            "pass_rate": round(row.passed / total, 4) if total else 0.0,
            "total": total,
            "passed": row.passed or 0,
        }


# ── Mappers ───────────────────────────────────────────────────────────────────

def _ds_to_model(d: Dataset) -> DatasetModel:
    return DatasetModel(
        id=d.id, org_id=d.org_id, name=d.name, description=d.description,
        dataset_type=d.dataset_type, created_by=d.created_by,
        metadata_=d.metadata, created_at=d.created_at, updated_at=d.updated_at,
    )


def _model_to_ds(m: DatasetModel) -> Dataset:
    return Dataset(
        id=m.id, org_id=m.org_id, name=m.name, description=m.description,
        dataset_type=m.dataset_type, created_by=m.created_by,
        metadata=m.metadata_ or {}, created_at=m.created_at, updated_at=m.updated_at,
    )


def _item_to_model(i: DatasetItem) -> DatasetItemModel:
    return DatasetItemModel(
        id=i.id, dataset_id=i.dataset_id, input_=i.input,
        expected_output_=i.expected_output, context=i.context,
        metadata_=i.metadata, created_at=i.created_at,
    )


def _model_to_item(m: DatasetItemModel) -> DatasetItem:
    return DatasetItem(
        id=m.id, dataset_id=m.dataset_id, input=m.input_ or {},
        expected_output=m.expected_output_, context=m.context or [],
        metadata=m.metadata_ or {}, created_at=m.created_at,
    )


def _run_to_model(r: EvaluationRun) -> EvaluationRunModel:
    return EvaluationRunModel(
        id=r.id, org_id=r.org_id, agent_id=r.agent_id,
        agent_version_id=r.agent_version_id, dataset_id=r.dataset_id,
        name=r.name, description=r.description, status=r.status.value,
        eval_type=r.eval_type.value, config=r.config,
        total_items=r.total_items, completed_items=r.completed_items,
        failed_items=r.failed_items, aggregate_scores=r.aggregate_scores,
        started_at=r.started_at, completed_at=r.completed_at,
        created_by=r.created_by, created_at=r.created_at,
    )


def _model_to_run(m: EvaluationRunModel) -> EvaluationRun:
    return EvaluationRun(
        id=m.id, org_id=m.org_id, agent_id=m.agent_id,
        agent_version_id=m.agent_version_id, dataset_id=m.dataset_id,
        name=m.name, description=m.description,
        status=EvaluationStatus(m.status), eval_type=EvaluationType(m.eval_type),
        config=m.config or {}, total_items=m.total_items,
        completed_items=m.completed_items, failed_items=m.failed_items,
        aggregate_scores=m.aggregate_scores or {}, started_at=m.started_at,
        completed_at=m.completed_at, created_by=m.created_by, created_at=m.created_at,
    )


def _result_to_model(r: EvaluationResult) -> EvaluationResultModel:
    return EvaluationResultModel(
        id=r.id, eval_run_id=r.eval_run_id, execution_id=r.execution_id,
        dataset_item_id=r.dataset_item_id,
        correctness_score=r.correctness_score, relevance_score=r.relevance_score,
        faithfulness_score=r.faithfulness_score, helpfulness_score=r.helpfulness_score,
        hallucination_score=r.hallucination_score, context_precision=r.context_precision,
        context_recall=r.context_recall, answer_relevancy=r.answer_relevancy,
        custom_scores=r.custom_scores, reasoning=r.reasoning, passed=r.passed,
        created_at=r.created_at,
    )


def _model_to_result(m: EvaluationResultModel) -> EvaluationResult:
    return EvaluationResult(
        id=m.id, eval_run_id=m.eval_run_id, execution_id=m.execution_id,
        dataset_item_id=m.dataset_item_id,
        correctness_score=m.correctness_score, relevance_score=m.relevance_score,
        faithfulness_score=m.faithfulness_score, helpfulness_score=m.helpfulness_score,
        hallucination_score=m.hallucination_score, context_precision=m.context_precision,
        context_recall=m.context_recall, answer_relevancy=m.answer_relevancy,
        custom_scores=m.custom_scores or {}, reasoning=m.reasoning, passed=m.passed,
        created_at=m.created_at,
    )

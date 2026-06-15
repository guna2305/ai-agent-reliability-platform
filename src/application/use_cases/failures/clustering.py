"""Failure clustering orchestration + semantic search.

assign_clusters() is DB-independent (testable): given reports that already
carry embeddings, it runs k-means and returns {report_id: cluster_id}.

ClusterFailuresUseCase wires Ollama embedding generation + persistence around it.
SearchFailuresUseCase ranks failures by cosine similarity to a query embedding.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.application.interfaces.repositories import FailureReportRepository
from src.domain.entities import FailureReport
from src.infrastructure.ai.clustering import cosine_similarity, kmeans


def assign_clusters(
    reports: list[FailureReport],
    k: int | None = None,
) -> dict[str, int]:
    """Run k-means over reports that have embeddings; return report_id -> cluster_id."""
    embedded = [r for r in reports if r.embedding_vector]
    if not embedded:
        return {}
    vectors = [r.embedding_vector for r in embedded]  # type: ignore[misc]
    result = kmeans(vectors, k=k)
    return {r.id: label for r, label in zip(embedded, result.labels)}


def _failure_text(report: FailureReport) -> str:
    parts = [report.title, report.description]
    if report.root_cause:
        parts.append(report.root_cause)
    return " ".join(parts)


@dataclass
class ClusterRunResult:
    clustered: int
    embedded: int
    k: int


class ClusterFailuresUseCase:
    """Generate missing embeddings (Ollama) then re-cluster all org failures."""

    def __init__(self, repo: FailureReportRepository) -> None:
        self._repo = repo

    async def execute(self, org_id: str, k: int | None = None) -> ClusterRunResult:
        from src.infrastructure.ai.providers import embed_ollama

        reports = await self._repo.list_by_org(org_id, limit=10_000, offset=0)

        # 1. Backfill embeddings for reports that don't have one yet
        newly_embedded = 0
        for report in reports:
            if not report.embedding_vector:
                try:
                    vector = await embed_ollama(_failure_text(report))
                    report.set_embedding(vector)
                    await self._repo.update(report)
                    newly_embedded += 1
                except Exception:
                    continue  # Ollama unavailable for this one; skip

        # 2. Cluster everything that now has an embedding
        embedded = [r for r in reports if r.embedding_vector]
        if not embedded:
            return ClusterRunResult(clustered=0, embedded=0, k=0)

        vectors = [r.embedding_vector for r in embedded]  # type: ignore[misc]
        result = kmeans(vectors, k=k)
        for report, label in zip(embedded, result.labels):
            report.assign_cluster(label)
            await self._repo.update(report)

        return ClusterRunResult(clustered=len(embedded), embedded=newly_embedded, k=result.k)


class SearchFailuresUseCase:
    """Semantic search: rank org failures by similarity to a free-text query."""

    def __init__(self, repo: FailureReportRepository) -> None:
        self._repo = repo

    async def execute(self, org_id: str, query: str, top_k: int = 10) -> list[tuple[FailureReport, float]]:
        from src.infrastructure.ai.providers import embed_ollama

        reports = await self._repo.list_all_for_clustering(org_id)
        if not reports:
            return []

        try:
            query_vec = await embed_ollama(query)
        except Exception:
            return []

        scored = [
            (r, cosine_similarity(query_vec, r.embedding_vector))  # type: ignore[arg-type]
            for r in reports
            if r.embedding_vector
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]

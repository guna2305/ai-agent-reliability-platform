"""Unit tests for assign_clusters (DB-independent failure clustering)."""
from src.application.use_cases.failures import assign_clusters
from src.domain.entities import FailureReport
from src.domain.value_objects import FailureSeverity, FailureType


def _report(rid: str, embedding=None) -> FailureReport:
    r = FailureReport.create(
        org_id="org-1",
        execution_id=f"exec-{rid}",
        failure_type=FailureType.TOOL,
        severity=FailureSeverity.MEDIUM,
        title=f"Failure {rid}",
        description="desc",
    )
    r.id = rid
    if embedding is not None:
        r.set_embedding(embedding)
    return r


def test_assign_clusters_empty():
    assert assign_clusters([]) == {}


def test_assign_clusters_skips_unembedded():
    reports = [_report("a"), _report("b")]  # no embeddings
    assert assign_clusters(reports) == {}


def test_assign_clusters_groups_similar():
    reports = [
        _report("a1", [1.0, 1.0]),
        _report("a2", [1.1, 0.9]),
        _report("b1", [-1.0, -1.0]),
        _report("b2", [-0.9, -1.1]),
    ]
    mapping = assign_clusters(reports, k=2)
    assert set(mapping.keys()) == {"a1", "a2", "b1", "b2"}
    # a1/a2 together, b1/b2 together
    assert mapping["a1"] == mapping["a2"]
    assert mapping["b1"] == mapping["b2"]
    assert mapping["a1"] != mapping["b1"]


def test_assign_clusters_mixed_embedded_and_not():
    reports = [
        _report("a1", [1.0, 1.0]),
        _report("no-emb"),  # excluded
        _report("a2", [1.1, 0.9]),
    ]
    mapping = assign_clusters(reports, k=1)
    assert "no-emb" not in mapping
    assert set(mapping.keys()) == {"a1", "a2"}

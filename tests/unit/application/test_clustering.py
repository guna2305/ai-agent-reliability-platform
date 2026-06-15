"""Unit tests for pure-Python k-means clustering."""
from src.infrastructure.ai.clustering import cosine_similarity, kmeans


def test_kmeans_empty():
    result = kmeans([])
    assert result.k == 0
    assert result.labels == []


def test_kmeans_single_vector():
    result = kmeans([[1.0, 2.0, 3.0]], k=1)
    assert result.k == 1
    assert result.labels == [0]


def test_kmeans_separates_two_groups():
    # Two clearly separated clusters in 2D
    vectors = [
        [1.0, 1.0], [1.1, 0.9], [0.9, 1.1],     # group A
        [-1.0, -1.0], [-1.1, -0.9], [-0.9, -1.1],  # group B
    ]
    result = kmeans(vectors, k=2, seed=1)
    # The three A points share a label; the three B points share the other
    assert len(set(result.labels[:3])) == 1
    assert len(set(result.labels[3:])) == 1
    assert result.labels[0] != result.labels[3]


def test_kmeans_k_capped_at_n():
    vectors = [[1.0, 0.0], [0.0, 1.0]]
    result = kmeans(vectors, k=10)
    assert result.k <= 2


def test_kmeans_deterministic_with_seed():
    vectors = [[float(i), float(i % 3)] for i in range(20)]
    r1 = kmeans(vectors, k=3, seed=42)
    r2 = kmeans(vectors, k=3, seed=42)
    assert r1.labels == r2.labels


def test_kmeans_inertia_non_negative():
    vectors = [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]]
    result = kmeans(vectors, k=2)
    assert result.inertia >= 0.0


def test_cosine_similarity_identical():
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1.0


def test_cosine_similarity_orthogonal():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_similarity_zero_vector():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

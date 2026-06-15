"""Pure-Python k-means clustering for failure embeddings.

No numpy/sklearn dependency — keeps the image small and the logic fully
unit-testable. Operates on L2-normalized vectors so Euclidean distance is
monotonic with cosine distance (standard trick for text embeddings).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class ClusterResult:
    labels: list[int]          # cluster index per input vector
    centroids: list[list[float]]
    k: int
    inertia: float             # sum of squared distances to assigned centroid


def _l2_normalize(v: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in v))
    if norm == 0:
        return v
    return [x / norm for x in v]


def _sq_dist(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _suggest_k(n: int) -> int:
    """Heuristic cluster count: sqrt(n/2), bounded to [1, 10]."""
    if n <= 2:
        return 1
    return max(1, min(10, int(math.sqrt(n / 2))))


def _kmeans_plus_plus_init(vectors: list[list[float]], k: int, rng: random.Random) -> list[list[float]]:
    centroids = [list(rng.choice(vectors))]
    while len(centroids) < k:
        # Distance of each point to its nearest existing centroid
        dists = [min(_sq_dist(v, c) for c in centroids) for v in vectors]
        total = sum(dists)
        if total == 0:
            # All remaining points coincide with centroids; pad with random picks
            centroids.append(list(rng.choice(vectors)))
            continue
        # Weighted choice proportional to squared distance (k-means++)
        threshold = rng.random() * total
        cumulative = 0.0
        for v, d in zip(vectors, dists):
            cumulative += d
            if cumulative >= threshold:
                centroids.append(list(v))
                break
    return centroids


def kmeans(
    vectors: list[list[float]],
    k: int | None = None,
    max_iter: int = 50,
    seed: int = 42,
) -> ClusterResult:
    """Cluster vectors with k-means++ initialization.

    Returns a ClusterResult. If k is None, a heuristic count is chosen.
    """
    n = len(vectors)
    if n == 0:
        return ClusterResult(labels=[], centroids=[], k=0, inertia=0.0)

    normalized = [_l2_normalize(v) for v in vectors]
    k = k or _suggest_k(n)
    k = max(1, min(k, n))  # cannot have more clusters than points

    rng = random.Random(seed)
    centroids = _kmeans_plus_plus_init(normalized, k, rng)
    labels = [0] * n

    for _ in range(max_iter):
        # Assignment step
        changed = False
        for i, v in enumerate(normalized):
            best, best_d = 0, float("inf")
            for ci, c in enumerate(centroids):
                d = _sq_dist(v, c)
                if d < best_d:
                    best, best_d = ci, d
            if labels[i] != best:
                labels[i] = best
                changed = True

        # Update step
        new_centroids: list[list[float]] = []
        dim = len(normalized[0])
        for ci in range(k):
            members = [normalized[i] for i in range(n) if labels[i] == ci]
            if not members:
                # Re-seed empty cluster to a random point
                new_centroids.append(list(rng.choice(normalized)))
                continue
            centroid = [sum(m[d] for m in members) / len(members) for d in range(dim)]
            new_centroids.append(_l2_normalize(centroid))
        centroids = new_centroids

        if not changed:
            break

    inertia = sum(_sq_dist(normalized[i], centroids[labels[i]]) for i in range(n))
    return ClusterResult(labels=labels, centroids=centroids, k=k, inertia=round(inertia, 6))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return round(dot / (mag_a * mag_b), 6)

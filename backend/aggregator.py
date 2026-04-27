"""FedAvg-style aggregation helpers.

`average_flat_weights` accepts an optional `sample_counts` list. When provided,
each node's weights contribute proportionally to its data size — the standard
FedAvg formulation that handles unequal partitions correctly. When omitted,
it falls back to plain equal-weight averaging (useful for showing the
contrast in the demo: weighted vs naive aggregation).
"""
from typing import List, Optional


def average_flat_weights(
    list_of_flat: List[List[float]],
    sample_counts: Optional[List[int]] = None,
) -> List[float]:
    if not list_of_flat:
        return []

    n = len(list_of_flat)
    length = len(list_of_flat[0])

    if sample_counts is None or sum(sample_counts) <= 0:
        sample_counts = [1] * n

    total = float(sum(sample_counts))
    avg = [0.0] * length
    for w, c in zip(list_of_flat, sample_counts):
        weight = float(c) / total
        for i, val in enumerate(w):
            avg[i] += float(val) * weight
    return avg

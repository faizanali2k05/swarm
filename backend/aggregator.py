"""Aggregation helpers for swarm-style averaging."""
from typing import List


def average_flat_weights(list_of_flat: List[List[float]]):
    """Simple element-wise average of flattened weight lists."""
    if not list_of_flat:
        return []
    n = len(list_of_flat)
    length = len(list_of_flat[0])
    avg = [0.0] * length
    for w in list_of_flat:
        for i, val in enumerate(w):
            avg[i] += float(val) / n
    return avg

import numpy as np
from typing import Iterable, List


def generate_zipf_queries(
    keys: List[str],
    alpha: float,
    n_queries: int,
    non_member_keys: List[str],
    non_member_ratio: float = 0.1,
    seed: int = 123,
) -> Iterable[str]:
    if alpha <= 0:
        raise ValueError("alpha must be positive for Zipf distribution.")
    if not keys:
        return []
    if non_member_ratio > 0 and len(non_member_keys) == 0:
        raise ValueError("non_member_ratio > 0 but non_member_keys is empty")

    rng = np.random.default_rng(seed)
    ranks = np.arange(1, len(keys) + 1)
    weights = 1 / np.power(ranks, alpha)
    probs = weights / weights.sum()

    for _ in range(n_queries):
        if non_member_ratio > 0 and rng.random() < non_member_ratio:
            yield non_member_keys[rng.integers(0, len(non_member_keys))]
        else:
            idx = rng.choice(len(keys), p=probs)
            yield keys[idx]


def validate_zipf_queries(
    queries: List[str], members: List[str], non_members: List[str], top_n: int = 10
) -> dict:
    from collections import Counter

    member_set = set(members)
    non_member_set = set(non_members)
    non_member_count = sum(1 for q in queries if q in non_member_set)
    non_member_fraction = non_member_count / len(queries) if queries else 0.0

    member_queries = [q for q in queries if q in member_set]
    top_frequencies = Counter(member_queries).most_common(top_n)

    return {
        "non_member_fraction": non_member_fraction,
        "non_member_count": non_member_count,
        "total_queries": len(queries),
        "top_frequencies": top_frequencies,
    }



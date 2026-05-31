from typing import Any

BACKEND_MISS_SPINS = 0


def _miss_penalty(spins: int) -> int:
    x = 0
    for _ in range(spins):
        x += 1
    return x


def query_no_filter(ht: Any, key: str, miss_spins: int = BACKEND_MISS_SPINS) -> bool:
    result = ht.contains(key)
    if not result and miss_spins > 0:
        _ = _miss_penalty(miss_spins)
    return result


def query_with_filter(filter_obj: Any, ht: Any, key: str, miss_spins: int = BACKEND_MISS_SPINS) -> bool:
    if filter_obj.contains(key):
        result = ht.contains(key)
        if not result and miss_spins > 0:
            _ = _miss_penalty(miss_spins)
        return result
    return False

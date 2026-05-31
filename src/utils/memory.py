import sys


def get_memory_bytes(obj) -> int:
    try:
        return sys.getsizeof(obj)
    except TypeError:
        return 0


def bits_per_key(memory_bytes: int, n_keys: int) -> float:
    if n_keys == 0:
        return 0.0
    return memory_bytes * 8 / n_keys

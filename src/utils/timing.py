import time
from typing import Callable, Tuple, TypeVar

T = TypeVar("T")


def time_function(fn: Callable[..., T], *args, **kwargs) -> Tuple[T, float]:
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed

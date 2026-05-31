import math
import hashlib
from typing import Iterable, Optional


class CountingBloomFilter:

    def __init__(
        self,
        n: Optional[int] = None,
        fp_target: Optional[float] = None,
        counter_bits: int = 4,
        m: Optional[int] = None,
        k: Optional[int] = None,
    ):
        if m is None or k is None:
            if n is None or fp_target is None:
                raise ValueError("Provide either (m, k) or (n, fp_target).")
            if not (0 < fp_target < 1):
                raise ValueError("fp_target must be between 0 and 1.")
            m_float = -n * math.log(fp_target) / (math.log(2) ** 2)
            self.m = int(math.ceil(m_float))
            self.k = int(math.ceil((self.m / n) * math.log(2)))
        else:
            self.m = int(m)
            self.k = int(k)
        if self.k <= 0 or self.m <= 0:
            raise ValueError("m and k must be positive.")
        if counter_bits <= 0:
            raise ValueError("counter_bits must be positive.")

        self.counter_bits = counter_bits
        self.max_counter = (1 << counter_bits) - 1
        self.counters = [0] * self.m

    def _hashes(self, key: str) -> Iterable[int]:
        key_bytes = key.encode("utf-8")
        h1_digest = hashlib.sha256(key_bytes + b"h1").digest()
        h2_digest = hashlib.sha256(key_bytes + b"h2").digest()
        h1 = int.from_bytes(h1_digest, "big") % self.m
        h2 = int.from_bytes(h2_digest, "big") % self.m
        if h2 == 0:
            h2 = 1
        for i in range(self.k):
            yield (h1 + i * h2) % self.m

    def insert(self, key: str) -> None:
        for idx in self._hashes(key):
            if self.counters[idx] < self.max_counter:
                self.counters[idx] += 1

    def contains(self, key: str) -> bool:
        return all(self.counters[idx] > 0 for idx in self._hashes(key))

    def memory_bytes(self) -> int:
        counter_bits_total = self.m * self.counter_bits
        return math.ceil(counter_bits_total / 8)

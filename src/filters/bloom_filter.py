import math
import hashlib
from typing import Iterable, Optional


class BloomFilter:

    def __init__(
        self,
        n: Optional[int] = None,
        fp_target: Optional[float] = None,
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

        self.bits = bytearray((self.m + 7) // 8)

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

    def _set_bit(self, idx: int) -> None:
        byte_idx, bit_idx = divmod(idx, 8)
        self.bits[byte_idx] |= 1 << bit_idx

    def _get_bit(self, idx: int) -> bool:
        byte_idx, bit_idx = divmod(idx, 8)
        return bool(self.bits[byte_idx] & (1 << bit_idx))

    def insert(self, key: str) -> None:
        for idx in self._hashes(key):
            self._set_bit(idx)

    def contains(self, key: str) -> bool:
        return all(self._get_bit(idx) for idx in self._hashes(key))

    def memory_bytes(self) -> int:
        return len(self.bits)

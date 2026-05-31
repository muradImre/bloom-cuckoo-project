import hashlib
import random
from typing import List, Optional


class CuckooFilter:

    def __init__(
        self,
        num_buckets: int,
        bucket_size: int,
        fingerprint_bits: int,
        max_kicks: int = 500,
    ):
        if num_buckets <= 0 or bucket_size <= 0:
            raise ValueError("num_buckets and bucket_size must be positive.")
        if fingerprint_bits <= 0:
            raise ValueError("fingerprint_bits must be positive.")
        self.num_buckets = num_buckets
        self.bucket_size = bucket_size
        self.fingerprint_bits = fingerprint_bits
        self.max_kicks = max_kicks
        self.mask = (1 << fingerprint_bits) - 1
        self.buckets: List[List[int]] = [[] for _ in range(num_buckets)]
        self.failed_inserts = 0

    def _fingerprint(self, key: str) -> int:
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        fp = int.from_bytes(digest, "big") & self.mask
        return fp or 1

    def _bucket_index(self, key: str) -> int:
        return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % self.num_buckets

    def _alt_index(self, index: int, fingerprint: int) -> int:
        return (index ^ (fingerprint * 0x5bd1e995)) % self.num_buckets

    def _place_in_bucket(self, bucket_idx: int, fingerprint: int) -> bool:
        bucket = self.buckets[bucket_idx]
        if len(bucket) < self.bucket_size:
            bucket.append(fingerprint)
            return True
        return False

    def insert(self, key: str) -> bool:
        fp = self._fingerprint(key)
        i1 = self._bucket_index(key)
        i2 = self._alt_index(i1, fp)

        if self._place_in_bucket(i1, fp) or self._place_in_bucket(i2, fp):
            return True

        idx = random.choice([i1, i2])
        cur_fp = fp
        for _ in range(self.max_kicks):
            bucket = self.buckets[idx]
            victim_pos = random.randrange(len(bucket))
            bucket[victim_pos], cur_fp = cur_fp, bucket[victim_pos]
            idx = self._alt_index(idx, cur_fp)
            if self._place_in_bucket(idx, cur_fp):
                return True

        self.failed_inserts += 1
        return False

    def contains(self, key: str) -> bool:
        fp = self._fingerprint(key)
        i1 = self._bucket_index(key)
        i2 = self._alt_index(i1, fp)
        return fp in self.buckets[i1] or fp in self.buckets[i2]

    def memory_bytes(self) -> int:
        total_bits = self.num_buckets * self.bucket_size * self.fingerprint_bits
        return (total_bits + 7) // 8

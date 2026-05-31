import sys
from typing import Dict


class HashTableIndex:

    def __init__(self):
        self.store: Dict[str, bool] = {}

    def insert(self, key: str) -> None:
        self.store[key] = True

    def contains(self, key: str) -> bool:
        return key in self.store

    def memory_bytes(self) -> int:
        return sys.getsizeof(self.store) + len(self.store) * sys.getsizeof("")

import random
from typing import List, Tuple


def generate_datasets(
    n_keys: int,
    non_member_multiplier: float = 1.0,
    seed: int = 42,
) -> Tuple[List[str], List[str]]:
    rng = random.Random(seed)
    members = [f"key_{i}" for i in range(n_keys)]

    non_members = []
    needed = int(n_keys * non_member_multiplier)
    current = n_keys
    while len(non_members) < needed:
        candidate = f"key_{current}"
        non_members.append(candidate)
        current += 1
    rng.shuffle(non_members)
    return members, non_members



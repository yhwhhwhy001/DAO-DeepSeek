"""Pattern Hasher — shape hash computation and pattern registry."""
import hashlib
from dataclasses import dataclass, field

SHAPE_HASH_LEN = 12


def compute_shape_hash(positions: list[tuple[int, int]], centroid: tuple[float, float]) -> str:
    rel = sorted((int(p[0] - centroid[0]), int(p[1] - centroid[1])) for p in positions)
    key = repr(rel).encode()
    return hashlib.sha256(key).hexdigest()[:SHAPE_HASH_LEN]


@dataclass
class PatternRecord:
    shape_hash: str
    first_seen: int = 0
    total_occurrences: int = 0
    max_concurrent: int = 0
    locations: list[tuple[int, int]] = field(default_factory=list)
    _tick_counts: dict[int, int] = field(default_factory=dict)

    def record_occurrence(self, tick: int, location: tuple[int, int]) -> None:
        self.total_occurrences += 1
        if len(self.locations) < 20:
            self.locations.append(location)
        self._tick_counts[tick] = self._tick_counts.get(tick, 0) + 1
        if self._tick_counts[tick] > self.max_concurrent:
            self.max_concurrent = self._tick_counts[tick]


class PatternHasher:
    def __init__(self):
        self.patterns: dict[str, PatternRecord] = {}

    def register(self, shape_hash: str, tick: int, location: tuple[int, int]) -> None:
        if not shape_hash:
            return
        if shape_hash not in self.patterns:
            self.patterns[shape_hash] = PatternRecord(
                shape_hash=shape_hash, first_seen=tick,
            )
        self.patterns[shape_hash].record_occurrence(tick, location)

    def get_top(self, n: int = 5) -> list[tuple[str, int]]:
        sorted_pats = sorted(
            self.patterns.items(),
            key=lambda kv: kv[1].total_occurrences, reverse=True,
        )
        return [(h, r.total_occurrences) for h, r in sorted_pats[:n]]

    def unique_count(self) -> int:
        return len(self.patterns)

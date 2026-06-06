"""Entropy Engine -- 3-layer entropy measurement and trend detection."""
import math
from collections import Counter
from src.grid import Grid
from src.event_bus import EventBus, EventType
from src.structure_detector import StructureDetector

TREND_WINDOW = 50


def compute_global_entropy(grid: Grid, num_types: int) -> float:
    if grid.alive_count == 0:
        return 0.0
    type_counts = Counter(c.type for c in grid.all_cells)
    total = grid.alive_count
    h = 0.0
    for t in range(num_types):
        p = type_counts.get(t, 0) / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def compute_local_entropy(grid: Grid, num_types: int) -> tuple[float, float]:
    if grid.alive_count == 0:
        return (0.0, 0.0)
    entropies = []
    for cell in grid.all_cells:
        neighbors = [n for n in grid.get_neighbors(cell.x, cell.y) if n is not None]
        nearby = Counter(n.type for n in neighbors)
        nearby[cell.type] += 1
        total = sum(nearby.values())
        h = 0.0
        for t in range(num_types):
            p = nearby.get(t, 0) / total
            if p > 0:
                h -= p * math.log2(p)
        entropies.append(h)
    if not entropies:
        return (0.0, 0.0)
    mean = sum(entropies) / len(entropies)
    var = sum((h - mean) ** 2 for h in entropies) / len(entropies)
    return (mean, var ** 0.5)


class EntropyEngine:
    def __init__(self, grid: Grid, bus: EventBus, detector: StructureDetector, num_types: int = 4):
        self.grid = grid
        self.bus = bus
        self.detector = detector
        self.num_types = num_types
        self.current_snapshot: dict | None = None
        self.current_trend: str = "steady"
        self._history: list[dict] = []
        bus.subscribe(EventType.TICK_END, self._on_tick_end)

    def _on_tick_end(self, event) -> None:
        tick = event.data["tick"]
        self.current_snapshot = self.snapshot(tick)
        self._history.append(self.current_snapshot)
        if tick % TREND_WINDOW == 0 and len(self._history) >= 2:
            new_trend = self._detect_trend()
            if new_trend != self.current_trend:
                self.bus.publish(EventType.TREND_CHANGED, {
                    "previous": self.current_trend, "current": new_trend,
                })
                self.current_trend = new_trend

    def snapshot(self, tick: int) -> dict:
        h_global = compute_global_entropy(self.grid, self.num_types)
        h_local_mean, h_local_std = compute_local_entropy(self.grid, self.num_types)

        structures = self.detector.get_active()
        h_struct = 0.0
        if structures:
            hash_counts = Counter(s.shape_hash for s in structures if s.shape_hash)
            total = sum(hash_counts.values())
            if total > 0:
                for count in hash_counts.values():
                    p = count / total
                    h_struct -= p * math.log2(p)

        return {
            "tick": tick,
            "global_entropy": h_global,
            "local_entropy_mean": h_local_mean,
            "local_entropy_std": h_local_std,
            "structure_entropy": h_struct,
            "stable_count": self.detector.stable_count,
            "active_count": self.detector.active_count,
        }

    def _detect_trend(self) -> str:
        if len(self._history) < 2:
            return "steady"
        current = self._history[-1]
        target_tick = current["tick"] - TREND_WINDOW
        prev = self._history[0]
        for h in reversed(self._history[:-1]):
            if h["tick"] <= target_tick:
                prev = h
                break
        d_local = current["local_entropy_mean"] - prev["local_entropy_mean"]
        d_stable = current["stable_count"] - prev["stable_count"]
        d_global = current["global_entropy"] - prev["global_entropy"]
        if d_local < -0.05 and d_stable > 0:
            return "ordering"
        if d_local > 0.05 and d_stable < 0:
            return "chaos"
        if d_global > 0.1:
            return "diversifying"
        return "steady"

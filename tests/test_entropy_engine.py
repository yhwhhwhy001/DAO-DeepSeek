"""Tests for Entropy Engine."""
import math
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus, EventType
from src.structure_detector import StructureDetector
from src.entropy_engine import EntropyEngine, compute_global_entropy, compute_local_entropy


class TestGlobalEntropy:
    def test_uniform(self):
        g = Grid(width=10, height=10, boundary="toroidal")
        for t in range(4):
            g.place(Cell(x=t, y=0, type=t))
        h = compute_global_entropy(g, num_types=4)
        assert abs(h - math.log2(4)) < 0.01

    def test_single_type_zero(self):
        g = Grid(width=10, height=10, boundary="toroidal")
        g.place(Cell(x=0, y=0, type=1))
        g.place(Cell(x=1, y=1, type=1))
        assert compute_global_entropy(g, num_types=4) == 0.0

    def test_empty_zero(self):
        g = Grid(width=10, height=10, boundary="toroidal")
        assert compute_global_entropy(g, num_types=4) == 0.0


class TestLocalEntropy:
    def test_same_type_low(self):
        g = Grid(width=10, height=10, boundary="toroidal")
        g.place(Cell(x=5, y=5, type=1))
        for pos in g.positions_around(5, 5):
            g.place(Cell(x=pos[0], y=pos[1], type=1))
        mean_h, _ = compute_local_entropy(g, num_types=4)
        assert mean_h < 0.1

    def test_mixed_high(self):
        g = Grid(width=10, height=10, boundary="toroidal")
        g.place(Cell(x=5, y=5, type=0))
        types = [1, 1, 2, 2, 3, 3, 0, 1]
        for (x, y), t in zip(g.positions_around(5, 5), types):
            g.place(Cell(x=x, y=y, type=t))
        mean_h, _ = compute_local_entropy(g, num_types=4)
        assert mean_h > 1.0


class TestEntropyEngine:
    def test_snapshot_has_all_fields(self):
        g = Grid(width=10, height=10, boundary="toroidal")
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = EntropyEngine(g, bus, det, num_types=4)
        g.place(Cell(x=0, y=0, type=0))
        g.place(Cell(x=1, y=1, type=1))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 2, "total_energy": 6.0})
        snap = eng.current_snapshot
        assert snap is not None
        for key in ["tick", "global_entropy", "local_entropy_mean", "local_entropy_std",
                     "structure_entropy", "stable_count", "active_count"]:
            assert key in snap

    def test_global_entropy_rises_with_diversity(self):
        g = Grid(width=10, height=10, boundary="toroidal")
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = EntropyEngine(g, bus, det, num_types=4)
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 0, "total_energy": 0.0})
        h_empty = eng.current_snapshot["global_entropy"]
        g.place(Cell(x=0, y=0, type=0))
        g.place(Cell(x=1, y=1, type=1))
        g.place(Cell(x=2, y=2, type=2))
        g.place(Cell(x=3, y=3, type=3))
        bus.tick = 2
        bus.publish(EventType.TICK_END, {"tick": 2, "alive_count": 4, "total_energy": 12.0})
        assert eng.current_snapshot["global_entropy"] > h_empty

    def test_default_trend_steady(self):
        g = Grid(width=10, height=10, boundary="toroidal")
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = EntropyEngine(g, bus, det, num_types=4)
        assert eng.current_trend == "steady"

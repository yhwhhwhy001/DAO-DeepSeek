"""Tests for State Engine physics rules."""
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus, EventType
from src.state_engine import StateEngine, PhysicsConfig


def make_engine(**overrides):
    defaults = dict(
        decay_rate=1.0, drift_probability=0.0, fission_threshold=10.0,
        fusion_probability=0.0, energy_input=0, num_types=4, seed=42,
    )
    defaults.update(overrides)
    config = PhysicsConfig(**defaults)
    grid = Grid(width=20, height=20, boundary="toroidal")
    bus = EventBus()
    engine = StateEngine(config, grid, bus)
    return engine, grid, bus


def captured_events(bus, event_type):
    events = []
    bus.subscribe(event_type, lambda e: events.append(e))
    return events


class TestDecay:
    def test_reduces_energy(self):
        eng, grid, _ = make_engine()
        grid.place(Cell(x=5, y=5, energy=5.0))
        eng.apply_decay()
        assert grid.get(5, 5).energy == 4.0

    def test_kills_at_zero(self):
        eng, grid, bus = make_engine()
        destroyed = captured_events(bus, EventType.CELL_DESTROYED)
        grid.place(Cell(x=0, y=0, energy=1.0, id="doomed"))
        eng.apply_decay()
        assert grid.get(0, 0) is None
        assert any(e.data["cell_id"] == "doomed" for e in destroyed)

    def test_kills_below_zero(self):
        eng, grid, _ = make_engine()
        grid.place(Cell(x=0, y=0, energy=0.5))
        eng.apply_decay()
        assert grid.get(0, 0) is None


class TestDrift:
    def test_no_drift_at_zero_probability(self):
        eng, grid, _ = make_engine(drift_probability=0.0)
        grid.place(Cell(x=5, y=5, type=0))
        for pos in grid.positions_around(5, 5):
            grid.place(Cell(x=pos[0], y=pos[1], type=1))
        eng.apply_drift()
        assert grid.get(5, 5).type == 0

    def test_drifts_to_majority(self):
        eng, grid, _ = make_engine(drift_probability=1.0)
        grid.place(Cell(x=5, y=5, type=0))
        for pos in grid.positions_around(5, 5):
            grid.place(Cell(x=pos[0], y=pos[1], type=1))
        eng.apply_drift()
        assert grid.get(5, 5).type == 1

    def test_no_neighbors_no_change(self):
        eng, grid, _ = make_engine(drift_probability=1.0)
        grid.place(Cell(x=0, y=0, type=2))
        eng.apply_drift()
        assert grid.get(0, 0).type == 2


class TestFission:
    def test_splits_high_energy_cell(self):
        eng, grid, bus = make_engine(fission_threshold=5.0)
        created = captured_events(bus, EventType.CELL_CREATED)
        grid.place(Cell(x=5, y=5, energy=10.0, type=2))
        eng.apply_fission()
        assert grid.get(5, 5).energy == 5.0
        assert grid.alive_count == 2
        assert len(created) == 1
        assert created[0].data["type"] == 2

    def test_no_fission_below_threshold(self):
        eng, grid, _ = make_engine(fission_threshold=10.0)
        grid.place(Cell(x=5, y=5, energy=9.9))
        eng.apply_fission()
        assert grid.alive_count == 1

    def test_no_fission_when_surrounded(self):
        eng, grid, _ = make_engine(fission_threshold=5.0)
        grid.place(Cell(x=5, y=5, energy=10.0))
        for pos in grid.positions_around(5, 5):
            grid.place(Cell(x=pos[0], y=pos[1]))
        eng.apply_fission()
        assert grid.alive_count == 9


class TestFusion:
    def test_merges_same_type(self):
        eng, grid, _ = make_engine(fusion_probability=1.0)
        grid.place(Cell(x=5, y=5, type=1, energy=4.0, id="a"))
        grid.place(Cell(x=5, y=4, type=1, energy=3.0, id="b"))
        eng.apply_fusion()
        assert grid.alive_count == 1
        survivor = list(grid.all_cells)[0]
        assert survivor.energy == 7.0

    def test_no_fusion_different_types(self):
        eng, grid, _ = make_engine(fusion_probability=1.0)
        grid.place(Cell(x=5, y=5, type=1, energy=4.0))
        grid.place(Cell(x=5, y=4, type=2, energy=3.0))
        eng.apply_fusion()
        assert grid.alive_count == 2

    def test_no_fusion_low_energy(self):
        eng, grid, _ = make_engine(fusion_probability=1.0)
        grid.place(Cell(x=5, y=5, type=1, energy=0.5))
        grid.place(Cell(x=5, y=4, type=1, energy=0.5))
        eng.apply_fusion()
        assert grid.alive_count == 2


class TestInjection:
    def test_creates_cells_at_empty_positions(self):
        eng, grid, bus = make_engine(energy_input=10)
        created = captured_events(bus, EventType.CELL_CREATED)
        eng.apply_injection()
        assert grid.alive_count > 0
        assert len(created) > 0

    def test_zero_energy_input_does_nothing(self):
        eng, grid, _ = make_engine(energy_input=0)
        eng.apply_injection()
        assert grid.alive_count == 0

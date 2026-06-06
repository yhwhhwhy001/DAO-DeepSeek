"""决策引擎的测试。"""
import random
from src.cell import Cell
from src.grid import Grid
from src.decision_engine import DecisionEngine, DecidingCell
from src.ruleset import generate_random_ruleset


def make_grid(w=20, h=20):
    return Grid(width=w, height=h, boundary="toroidal")


class TestDecidingCell:
    def test_has_ruleset_and_q_engine(self):
        rng = random.Random(42)
        dc = DecidingCell(cell_id="c1", ruleset=generate_random_ruleset(rng))
        assert dc.cell_id == "c1"
        assert len(dc.ruleset.rules) >= 2
        assert dc.utility is not None

    def test_energy_history(self):
        rng = random.Random(42)
        dc = DecidingCell(cell_id="c1", ruleset=generate_random_ruleset(rng))
        dc.record_energy(5.0)
        dc.record_energy(4.5)
        dc.record_energy(4.0)
        assert len(dc.energy_history) == 3
        assert dc.energy_trend < 0


class TestDecisionEngine:
    def test_engine_registers_cells(self):
        rng = random.Random(42)
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="c1"))
        engine = DecisionEngine(g, seed=42)
        ruleset = generate_random_ruleset(rng)
        dc = engine.register_cell("c1", ruleset)
        assert "c1" in engine.cells

    def test_engine_does_not_double_register(self):
        rng = random.Random(42)
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="c1"))
        engine = DecisionEngine(g, seed=42)
        rs = generate_random_ruleset(rng)
        engine.register_cell("c1", rs)
        engine.register_cell("c1", rs)
        assert len(engine.cells) == 1

    def test_remove_cell(self):
        rng = random.Random(42)
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="c1"))
        engine = DecisionEngine(g, seed=42)
        engine.register_cell("c1", generate_random_ruleset(rng))
        engine.remove_cell("c1")
        assert "c1" not in engine.cells

    def test_inherit_on_fission(self):
        rng = random.Random(42)
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="parent"))
        engine = DecisionEngine(g, seed=42)
        parent_rs = generate_random_ruleset(rng)
        engine.register_cell("parent", parent_rs)
        child = engine.inherit_on_fission("parent", "child", rng)
        assert child.cell_id == "child"
        assert len(child.ruleset.rules) >= 2

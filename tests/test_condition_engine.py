"""条件引擎的测试。"""
from src.cell import Cell
from src.grid import Grid
from src.condition_engine import ConditionEngine, compute_state_vector, discretize_state


def make_grid(w=20, h=20):
    return Grid(width=w, height=h, boundary="toroidal")


class TestStateVector:
    def test_all_fields_present(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="a"))
        state = compute_state_vector(g.get(5, 5), g, structure_size=3,
                                      structure_stable=1, generation=0, max_energy=10.0)
        for f in ["local_energy_density", "same_type_ratio", "hostile_type_ratio",
                   "empty_slots", "energy_level", "energy_trend", "generation",
                   "age_normalized", "structure_size", "structure_stable"]:
            assert f in state, f"missing {f}"

    def test_single_cell_no_neighbors(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="a"))
        state = compute_state_vector(g.get(5, 5), g, structure_size=0,
                                      structure_stable=0, generation=0, max_energy=10.0)
        assert state["local_energy_density"] == 0.0
        assert state["same_type_ratio"] == 0.0
        assert state["empty_slots"] == 8

    def test_all_same_type_neighbors(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="a"))
        for pos in g.positions_around(5, 5):
            g.place(Cell(x=pos[0], y=pos[1], type=1, energy=3.0))
        state = compute_state_vector(g.get(5, 5), g, structure_size=8,
                                      structure_stable=0, generation=0, max_energy=10.0)
        assert state["same_type_ratio"] == 1.0
        assert state["hostile_type_ratio"] == 0.0


class TestDiscretize:
    def test_discretize_returns_string_key(self):
        state = {"energy_level": 0.5, "hostile_ratio": 0.3, "energy_trend": 0.0,
                 "same_type_ratio": 0.7, "empty_slots": 4, "structure_size": 5,
                 "generation": 0}
        key = discretize_state(state)
        assert isinstance(key, str)
        assert "_" in key

"""条件引擎 —— 细胞级环境状态向量计算。"""
from src.cell import Cell
from src.grid import Grid


def compute_state_vector(
    cell: Cell, grid: Grid, *,
    structure_size: int = 0,
    structure_stable: int = 0,
    generation: int = 0,
    max_energy: float = 10.0,
    age: int = 0,
    mean_age: float = 1.0,
) -> dict:
    neighbors = [n for n in grid.get_neighbors(cell.x, cell.y) if n is not None]
    empty = 8 - len(neighbors)

    if neighbors:
        local_energy = sum(n.energy for n in neighbors) / len(neighbors)
        same_type = sum(1 for n in neighbors if n.type == cell.type) / len(neighbors)
        hostile = 1.0 - same_type
    else:
        local_energy = 0.0
        same_type = 0.0
        hostile = 0.0

    energy_level = min(cell.energy / max(max_energy, 0.1), 1.0)
    age_norm = min(age / max(mean_age, 1.0), 1.0)

    return {
        "local_energy_density": local_energy,
        "same_type_ratio": same_type,
        "hostile_type_ratio": hostile,
        "empty_slots": float(empty),
        "energy_level": energy_level,
        "energy_trend": 0.0,
        "generation": float(generation),
        "age_normalized": age_norm,
        "structure_size": float(structure_size),
        "structure_stable": float(structure_stable),
    }


def discretize_state(state: dict) -> str:
    def bucket(val, thresholds):
        for i, t in enumerate(thresholds):
            if val <= t:
                return str(i)
        return str(len(thresholds))

    parts = [
        bucket(state.get("energy_level", 0.5), [0.33, 0.66]),
        bucket(state.get("hostile_ratio", 0.5), [0.33, 0.66]),
        bucket(state.get("energy_trend", 0.0), [-0.1, 0.1]),
        bucket(state.get("same_type_ratio", 0.5), [0.33, 0.66]),
        bucket(state.get("empty_slots", 4), [2, 5]),
        bucket(state.get("structure_size", 0), [3]),
        bucket(state.get("generation", 0), [1]),
    ]
    return "_".join(parts)


class ConditionEngine:
    def __init__(self):
        self.max_energy_observed: float = 10.0

    def get_state(self, cell: Cell, grid: Grid, **kwargs) -> dict:
        state = compute_state_vector(cell, grid, max_energy=self.max_energy_observed, **kwargs)
        if cell.energy > self.max_energy_observed:
            self.max_energy_observed = cell.energy
        return state

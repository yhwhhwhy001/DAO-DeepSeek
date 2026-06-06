"""Decision Engine — per-cell sense-decide-act-learn pipeline."""
import random
from dataclasses import dataclass
from src.cell import Cell
from src.grid import Grid
from src.ruleset import RuleSet, generate_random_ruleset, mutate_ruleset
from src.condition_engine import ConditionEngine, discretize_state
from src.action_engine import ActionEngine, ACTION_COST, VALID_ACTIONS
from src.utility_engine import UtilityEngine, compute_reward

MOVE_DIRECTIONS = {
    "MOVE_N": (0, -1), "MOVE_S": (0, 1), "MOVE_E": (1, 0), "MOVE_W": (-1, 0),
    "MOVE_NE": (1, -1), "MOVE_NW": (-1, -1), "MOVE_SE": (1, 1), "MOVE_SW": (-1, 1),
}


@dataclass
class DecidingCell:
    cell_id: str
    ruleset: RuleSet
    utility: UtilityEngine | None = None
    energy_history: list[float] | None = None
    age: int = 0
    generation: int = 0
    last_state_key: str = ""
    last_action: str = "STAY"
    prev_structure_size: int = 0
    was_near_death: bool = False

    def __post_init__(self):
        if self.utility is None:
            self.utility = UtilityEngine()
        if self.energy_history is None:
            self.energy_history = []

    @property
    def energy_trend(self) -> float:
        if len(self.energy_history) < 2:
            return 0.0
        recent = self.energy_history[-5:]
        if len(recent) < 2:
            return 0.0
        n = len(recent)
        x_mean = (n - 1) / 2.0
        y_mean = sum(recent) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(recent))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0.0
        return max(-1.0, min(1.0, slope))

    def record_energy(self, energy: float) -> None:
        self.energy_history.append(energy)
        if len(self.energy_history) > 20:
            self.energy_history = self.energy_history[-20:]


class DecisionEngine:
    def __init__(self, grid: Grid, seed: int = 42):
        self.grid = grid
        self.cells: dict[str, DecidingCell] = {}
        self.condition = ConditionEngine()
        self.action_engine = ActionEngine()
        self._rng = random.Random(seed)
        self._detector = None  # set externally

    def register_cell(self, cell_id: str, ruleset: RuleSet) -> DecidingCell:
        if cell_id in self.cells:
            return self.cells[cell_id]
        dc = DecidingCell(cell_id=cell_id, ruleset=ruleset)
        self.cells[cell_id] = dc
        return dc

    def remove_cell(self, cell_id: str) -> None:
        self.cells.pop(cell_id, None)

    def inherit_on_fission(self, parent_id: str, child_id: str,
                           rng: random.Random) -> DecidingCell:
        parent = self.cells.get(parent_id)
        if parent:
            child_ruleset = mutate_ruleset(parent.ruleset, rng)
            child_utility = parent.utility.create_inherited()
            dc = DecidingCell(
                cell_id=child_id, ruleset=child_ruleset,
                utility=child_utility, generation=parent.generation + 1,
            )
        else:
            dc = DecidingCell(
                cell_id=child_id,
                ruleset=generate_random_ruleset(rng),
                generation=1,
            )
        self.cells[child_id] = dc
        return dc

    def step_cell(self, cell: Cell, dc: DecidingCell,
                  structure_size: int, structure_stable: int,
                  mean_age: float = 1.0) -> dict:
        state = self.condition.get_state(
            cell, self.grid,
            structure_size=structure_size,
            structure_stable=structure_stable,
            generation=dc.generation,
            age=dc.age,
            mean_age=max(mean_age, 1.0),
        )
        state["energy_trend"] = dc.energy_trend
        state_key = discretize_state(state)

        q_values = {}
        for a in VALID_ACTIONS:
            q_values[a] = dc.utility.get_q(state_key, a)

        action, _ = self.action_engine.select_action(
            state, dc.ruleset, q_values, self._rng,
        )

        if dc.last_state_key:
            prev_energy = dc.energy_history[-1] if dc.energy_history else cell.energy
            energy_delta = cell.energy - prev_energy
            prev_structure = dc.prev_structure_size
            joined = structure_size > prev_structure and prev_structure > 0
            lost = structure_size < prev_structure and prev_structure > 0
            near_death = dc.was_near_death and cell.energy > 1.0

            reward = compute_reward(
                energy_delta=energy_delta, survived=True,
                structure_joined=joined, structure_lost=lost,
                near_death_recovery=near_death, signals_received=0,
            )
            dc.utility.update(dc.last_state_key, dc.last_action, reward,
                              state_key, action)

        dc.last_state_key = state_key
        dc.last_action = action
        dc.prev_structure_size = structure_size
        dc.age += 1
        dc.record_energy(cell.energy)
        dc.was_near_death = cell.energy < 0.5

        return {"cell_id": cell.id, "action": action, "state_key": state_key}

    def step_all(self, grid, bus) -> None:
        """Run decision pipeline for all living cells."""
        for cell in list(grid.all_cells):
            if cell.id not in self.cells:
                # New cell from injection -- give it a random ruleset
                self.register_cell(cell.id, generate_random_ruleset(self._rng))

            dc = self.cells[cell.id]

            # Determine structure membership
            structure_size = 0
            structure_stable = 0
            if self._detector is not None:
                for s in self._detector.structures:
                    if cell.id in s.cells:
                        structure_size = len(s.cells)
                        structure_stable = 1 if s.status == "stable" else 0
                        break

            result = self.step_cell(cell, dc, structure_size, structure_stable)

            # Execute actions that directly affect physics
            action = result["action"]
            if action in MOVE_DIRECTIONS:
                dx, dy = MOVE_DIRECTIONS[action]
                new_x, new_y = grid._resolve(cell.x + dx, cell.y + dy)
                if new_x is not None and grid.is_empty(new_x, new_y):
                    grid.remove(cell.x, cell.y)
                    cell.x, cell.y = new_x, new_y
                    grid.place(cell)
                    cell.energy -= ACTION_COST.get(action, 0)
            elif action == "STAY":
                pass  # no cost, no change
            elif action == "SIGNAL":
                cell.energy -= ACTION_COST["SIGNAL"]
            # SPLIT/MERGE_REQUEST/TYPE_SHIFT modulate physics
            # (handled in state_engine via probabilities, but simplified here:
            #  just pay the cost)
            elif action in ("SPLIT", "MERGE_REQUEST", "TYPE_SHIFT"):
                cell.energy -= ACTION_COST.get(action, 0)

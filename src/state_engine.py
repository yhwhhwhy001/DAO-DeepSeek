"""State Engine -- 每 tick 对网格应用物理规则。"""
import random
from dataclasses import dataclass
from collections import Counter
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus, EventType


@dataclass
class PhysicsConfig:
    decay_rate: float = 1.0
    drift_probability: float = 0.05
    fission_threshold: float = 10.0
    fusion_probability: float = 0.01
    energy_input: int = 3
    num_types: int = 4
    seed: int = 42


class StateEngine:
    def __init__(self, config: PhysicsConfig, grid: Grid, bus: EventBus, map_engine=None, resource_engine=None):
        self.config = config
        self.grid = grid
        self.bus = bus
        self.map_engine = map_engine
        self.resource_engine = resource_engine
        self._rng = random.Random(config.seed)

    # --- 规则 1：衰变 ---

    def apply_decay(self) -> None:
        to_kill: list[tuple[int, int]] = []
        for cell in list(self.grid.all_cells):
            old_energy = cell.energy
            cell.energy -= self.config.decay_rate
            self.bus.publish(EventType.STATE_CHANGED, {
                "cell_id": cell.id, "field": "energy",
                "old": old_energy, "new": cell.energy,
            })
            if cell.energy <= 0:
                if self.resource_engine is not None:
                    remnant_energy = (cell.energy + self.config.decay_rate) * 0.5
                    if remnant_energy > 0.01:
                        self.resource_engine.create(cell.x, cell.y, remnant_energy, cell.type)
                to_kill.append((cell.x, cell.y))
        for x, y in to_kill:
            cell = self.grid.remove(x, y)
            if cell:
                self.bus.publish(EventType.CELL_DESTROYED, {
                    "cell_id": cell.id, "x": x, "y": y, "reason": "decay",
                })

    # --- 规则 2：漂变 ---

    def apply_drift(self) -> None:
        for cell in list(self.grid.all_cells):
            if self._rng.random() >= self.config.drift_probability:
                continue
            neighbors = [n for n in self.grid.get_neighbors(cell.x, cell.y) if n is not None]
            if not neighbors:
                continue
            type_counts = Counter(n.type for n in neighbors)
            most_common = type_counts.most_common()
            top_count = most_common[0][1]
            candidates = [t for t, c in most_common if c == top_count]
            new_type = self._rng.choice(candidates)
            if new_type != cell.type:
                old_type = cell.type
                cell.type = new_type
                self.bus.publish(EventType.STATE_CHANGED, {
                    "cell_id": cell.id, "field": "type",
                    "old": old_type, "new": new_type,
                })

    # --- 规则 3：分裂 ---

    def apply_fission(self) -> None:
        for cell in list(self.grid.all_cells):
            if cell.energy <= self.config.fission_threshold:
                continue
            empty = self.grid.empty_positions_around(cell.x, cell.y)
            if not empty:
                continue
            child_pos = self._rng.choice(empty)
            old_energy = cell.energy
            cell.energy /= 2.0
            child = Cell(x=child_pos[0], y=child_pos[1],
                         type=cell.type, energy=cell.energy)
            self.grid.place(child)
            self.bus.publish(EventType.STATE_CHANGED, {
                "cell_id": cell.id, "field": "energy",
                "old": old_energy, "new": cell.energy,
            })
            self.bus.publish(EventType.CELL_CREATED, {
                "cell_id": child.id, "x": child.x, "y": child.y,
                "type": child.type, "energy": child.energy,
            })

    # --- 规则 4：融合 ---

    def apply_fusion(self) -> None:
        processed: set[str] = set()
        for cell in list(self.grid.all_cells):
            if cell.id in processed:
                continue
            if cell.energy <= 1.0:
                continue
            neighbors = [n for n in self.grid.get_neighbors(cell.x, cell.y)
                         if n is not None and n.id not in processed]
            for other in neighbors:
                if other.type != cell.type or other.energy <= 1.0:
                    continue
                if self._rng.random() >= self.config.fusion_probability:
                    continue
                old_energy = cell.energy
                cell.energy += other.energy
                self.grid.remove(other.x, other.y)
                processed.add(cell.id)
                processed.add(other.id)
                self.bus.publish(EventType.CELL_DESTROYED, {
                    "cell_id": other.id, "x": other.x, "y": other.y, "reason": "fusion",
                })
                self.bus.publish(EventType.STATE_CHANGED, {
                    "cell_id": cell.id, "field": "energy",
                    "old": old_energy, "new": cell.energy,
                })
                break

    # --- 规则 5：注入 ---

    def apply_injection(self) -> None:
        for _ in range(self.config.energy_input):
            pos = self.grid.random_empty_position()
            if pos is None:
                cells = list(self.grid.all_cells)
                if not cells:
                    return
                target = self._rng.choice(cells)
                old_energy = target.energy
                target.energy += 1.0
                self.bus.publish(EventType.STATE_CHANGED, {
                    "cell_id": target.id, "field": "energy",
                    "old": old_energy, "new": target.energy,
                })
            else:
                multiplier = 1.0
                if self.map_engine is not None:
                    multiplier = self.map_engine.get_multiplier(pos[0], pos[1])
                new_type = self._rng.randrange(self.config.num_types)
                initial_energy = 1.0 * multiplier
                if self.resource_engine is not None:
                    absorbed = self.resource_engine.absorb(pos[0], pos[1], new_type, fraction=1.0)
                    initial_energy += absorbed
                cell = Cell(x=pos[0], y=pos[1], type=new_type, energy=initial_energy)
                self.grid.place(cell)
                self.bus.publish(EventType.CELL_CREATED, {
                    "cell_id": cell.id, "x": cell.x, "y": cell.y,
                    "type": cell.type, "energy": cell.energy,
                })

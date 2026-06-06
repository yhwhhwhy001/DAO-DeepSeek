"""World Engine — orchestrator that creates and wires all components."""
import random
import yaml
from pathlib import Path
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus
from src.state_engine import StateEngine, PhysicsConfig
from src.time_engine import TimeEngine


class WorldEngine:
    def __init__(self, config: dict):
        w = config["world"]
        p = config["physics"]
        init = config["initial"]

        self.config = config
        self.grid = Grid(width=w["width"], height=w["height"], boundary=w["boundary"])
        self.bus = EventBus()
        self.bus.subscribe_all(self._on_event)

        physics_config = PhysicsConfig(
            decay_rate=p["decay_rate"],
            drift_probability=p["drift_probability"],
            fission_threshold=p["fission_threshold"],
            fusion_probability=p["fusion_probability"],
            energy_input=p["energy_input"],
            num_types=p["num_types"],
            seed=w["seed"],
        )
        self.state_engine = StateEngine(physics_config, self.grid, self.bus)
        self.time_engine = TimeEngine(self.bus, self.state_engine)
        self._rng = random.Random(w["seed"])
        self._stats: list[dict] = []

        self._place_initial_cells(init)

    def _place_initial_cells(self, init: dict) -> None:
        count = init["cell_count"]
        min_e = init["min_energy"]
        max_e = init["max_energy"]
        num_types = self.config["physics"]["num_types"]

        for _ in range(count):
            pos = self.grid.random_empty_position()
            if pos is None:
                break
            cell = Cell(
                x=pos[0], y=pos[1],
                type=self._rng.randrange(num_types),
                energy=self._rng.uniform(min_e, max_e),
            )
            self.grid.place(cell)

    def run(self, ticks: int) -> list[dict]:
        self._stats = []
        self.time_engine.run(ticks)
        return self._stats

    def _on_event(self, event) -> None:
        if event.type.name == "TICK_END":
            self._stats.append(event.data)

    @classmethod
    def from_yaml(cls, path: str) -> "WorldEngine":
        with open(path) as f:
            config = yaml.safe_load(f)
        return cls(config)

# Phase 0: Universe Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal running universe — a 2D grid of cells governed by local physics rules, with terminal visualization, event-driven architecture, and experiment tracking.

**Architecture:** Five modules connected by an EventBus. World Engine orchestrates a synchronous tick loop. State Engine applies physics rules as pure functions. CLI Renderer displays grid state. Experiment Manager handles config and snapshots. No engine imports another engine directly — all communication through events.

**Tech Stack:** Python 3.14, numpy (grid storage), rich (terminal UI), PyYAML (config)

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

## File Structure

```
dao-genesis/
├── src/
│   ├── __init__.py
│   ├── cell.py              # Cell dataclass
│   ├── grid.py              # 2D grid, neighbor queries
│   ├── event_bus.py         # Pub/sub with typed events
│   ├── state_engine.py      # Physics rules (pure functions)
│   ├── time_engine.py       # Tick loop with phase ordering
│   ├── world_engine.py      # Orchestrator, owns grid+bus
│   └── cli/
│       ├── __init__.py
│       └── renderer.py      # Rich terminal display
├── experiments/
│   └── default.yaml         # Default experiment config
├── tests/
│   ├── __init__.py
│   ├── test_cell.py
│   ├── test_grid.py
│   ├── test_event_bus.py
│   ├── test_state_engine.py
│   ├── test_time_engine.py
│   └── test_world_engine.py
├── run.py                   # Entry point
└── requirements.txt
```

### Responsibility Map

| Module | Role | Depends On |
|--------|------|------------|
| `cell.py` | Pure data: id, type, energy, position | nothing |
| `grid.py` | Spatial container, 8-neighbor lookup, boundary | `cell.py` |
| `event_bus.py` | Typed pub/sub, wildcard listeners | nothing |
| `state_engine.py` | 5 physics rules as pure functions | `cell.py`, `grid.py` (read-only params) |
| `time_engine.py` | Tick counter, phase sequencer | `event_bus.py` |
| `world_engine.py` | Create grid, wire engines, run loop, collect stats | all above |
| `renderer.py` | Terminal grid + stats panel | `grid.py` (read-only), `event_bus.py` |

### Cell Data Model

```
id: str (uuid4)
type: int (0..num_types-1, currently 4)
energy: float
x: int
y: int
is_alive: energy > 0
position: (x, y)
```

### Grid Spec

- Fixed size: WIDTH x HEIGHT (configurable, default 80x40)
- Each cell occupies exactly one position (no overlapping)
- Boundary: toroidal (wrap-around) or walled (out-of-bounds returns None)
- Neighbors: Moore neighborhood (8 adjacent cells)
- Internal storage: dict `{(x, y): Cell}` backed by a 2D numpy array of Optional[str] (cell IDs)

### Physics Rules (Phase 0)

These are the ONLY rules. No fitness, no reward, no optimization, no intent.

| Rule | Trigger | Effect |
|------|---------|--------|
| **Decay** | Every tick, every cell | `energy -= decay_rate`. If `energy <= 0`, cell dies |
| **Drift** | `random() < drift_prob` per cell | Change type to most common neighbor type (8-neighbors) |
| **Fission** | `energy > fission_threshold` | Halve energy, spawn copy at random adjacent empty cell |
| **Fusion** | Two adjacent same-type cells, both energy > 1.0 | `random() < fusion_prob`: one survives with combined energy, other dies |
| **Injection** | Every tick | `energy_input` units of +1 energy distributed to random positions. Empty positions spawn new random-type cell |

Defaults: `decay_rate=1.0, drift_prob=0.05, fission_threshold=10.0, fusion_prob=0.01, energy_input=3, num_types=4`

### Tick Loop (per tick, in order)

```
1. Emit TICK_START
2. DECAY:     subtract energy, kill dead cells → emit CELL_DESTROYED
3. DRIFT:     type drift based on neighbors → emit STATE_CHANGED
4. FISSION:   split high-energy cells → emit CELL_CREATED
5. FUSION:    merge same-type neighbors → emit CELL_DESTROYED, STATE_CHANGED
6. INJECTION: add energy to random positions → emit CELL_CREATED or STATE_CHANGED
7. Emit TICK_END (with alive_count, total_energy stats)
```

All phases synchronous — each sees the state from the previous phase. Ordering is fixed for determinism.

### Event Types

```python
TICK_START      {"tick": int}
CELL_CREATED    {"cell_id": str, "x": int, "y": int, "type": int, "energy": float}
CELL_DESTROYED  {"cell_id": str, "x": int, "y": int, "reason": str}
STATE_CHANGED   {"cell_id": str, "field": str, "old": Any, "new": Any}
TICK_END        {"tick": int, "alive_count": int, "total_energy": float}
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `experiments/default.yaml`
- Create: `src/__init__.py`, `src/cli/__init__.py`
- Create: `tests/__init__.py`
- Create: `run.py` (skeleton)

- [ ] **Step 1: Create requirements.txt**

```txt
numpy>=2.0.0
rich>=13.0.0
pyyaml>=6.0
```

- [ ] **Step 2: Create default experiment config**

```yaml
experiment:
  name: "default"
  description: "Phase 0 baseline — primordial soup"

world:
  width: 80
  height: 40
  boundary: "toroidal"
  seed: 42

physics:
  decay_rate: 1.0
  drift_probability: 0.05
  fission_threshold: 10.0
  fusion_probability: 0.01
  energy_input: 3
  num_types: 4

initial:
  cell_count: 200
  min_energy: 3.0
  max_energy: 8.0

output:
  snapshot_interval: 100
  export_dir: "data/runs"
```

- [ ] **Step 3: Create __init__.py files and directory structure**

```bash
mkdir -p ~/Documents/Claude/dao-genesis/src/cli
mkdir -p ~/Documents/Claude/dao-genesis/tests
mkdir -p ~/Documents/Claude/dao-genesis/experiments
touch ~/Documents/Claude/dao-genesis/src/__init__.py
touch ~/Documents/Claude/dao-genesis/src/cli/__init__.py
touch ~/Documents/Claude/dao-genesis/tests/__init__.py
```

- [ ] **Step 4: Create run.py skeleton**

```python
"""DAO Genesis — Phase 0 Universe Engine."""

def main():
    print("DAO Genesis Phase 0 — Universe Engine")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Verify scaffold**

```bash
cd ~/Documents/Claude/dao-genesis && python run.py
```

Expected: `DAO Genesis Phase 0 — Universe Engine`

- [ ] **Step 6: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git init && git add -A && git commit -m "feat: scaffold Phase 0 project structure"
```

---

### Task 2: Cell Dataclass

**Files:**
- Create: `src/cell.py`
- Create: `tests/test_cell.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for Cell dataclass."""
import uuid
from src.cell import Cell


class TestCell:
    def test_defaults(self):
        c = Cell(x=5, y=10)
        assert c.x == 5
        assert c.y == 10
        assert c.type == 0
        assert c.energy == 0.0
        uuid.UUID(c.id)  # valid UUID

    def test_explicit_values(self):
        c = Cell(x=3, y=7, type=2, energy=5.5, id="test-id")
        assert c.type == 2
        assert c.energy == 5.5
        assert c.id == "test-id"

    def test_equality_by_id(self):
        c1 = Cell(x=0, y=0, id="same")
        c2 = Cell(x=10, y=20, id="same")
        c3 = Cell(x=0, y=0, id="diff")
        assert c1 == c2
        assert c1 != c3

    def test_hash_by_id(self):
        c1 = Cell(x=0, y=0, id="abc")
        c2 = Cell(x=10, y=20, id="abc")
        assert hash(c1) == hash(c2)
        assert len({c1, c2}) == 1

    def test_is_alive(self):
        assert Cell(x=0, y=0, energy=1.0).is_alive
        assert not Cell(x=0, y=1, energy=0.0).is_alive
        assert not Cell(x=0, y=2, energy=-0.5).is_alive

    def test_position_property(self):
        assert Cell(x=4, y=9).position == (4, 9)
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_cell.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.cell'`

- [ ] **Step 3: Write Cell implementation**

```python
"""Cell — the fundamental unit of the DAO Genesis universe."""
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Cell:
    x: int
    y: int
    type: int = 0
    energy: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return NotImplemented
        return self.id == other.id

    @property
    def is_alive(self) -> bool:
        return self.energy > 0.0

    @property
    def position(self) -> tuple[int, int]:
        return (self.x, self.y)
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_cell.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/cell.py tests/test_cell.py && git commit -m "feat: add Cell dataclass"
```

---

### Task 3: EventBus

**Files:**
- Create: `src/event_bus.py`
- Create: `tests/test_event_bus.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for EventBus."""
from src.event_bus import EventBus, EventType


class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.TICK_START, lambda e: received.append(e))
        bus.publish(EventType.TICK_START, {"tick": 1})
        assert len(received) == 1
        assert received[0].type == EventType.TICK_START
        assert received[0].data == {"tick": 1}

    def test_multiple_subscribers_same_event(self):
        bus = EventBus()
        results = []
        bus.subscribe(EventType.CELL_CREATED, lambda e: results.append("a"))
        bus.subscribe(EventType.CELL_CREATED, lambda e: results.append("b"))
        bus.publish(EventType.CELL_CREATED, {"cell_id": "x"})
        assert results == ["a", "b"]

    def test_unsubscribe_stops_receiving(self):
        bus = EventBus()
        results = []
        def h(e): results.append(e.data)
        bus.subscribe(EventType.TICK_END, h)
        bus.publish(EventType.TICK_END, {"tick": 1})
        bus.unsubscribe(EventType.TICK_END, h)
        bus.publish(EventType.TICK_END, {"tick": 2})
        assert len(results) == 1

    def test_publish_no_subscribers_does_not_raise(self):
        bus = EventBus()
        bus.publish(EventType.TICK_START, {"tick": 1})

    def test_wildcard_subscriber_receives_all(self):
        bus = EventBus()
        types = []
        bus.subscribe_all(lambda e: types.append(e.type))
        bus.publish(EventType.TICK_START, {})
        bus.publish(EventType.CELL_CREATED, {})
        bus.publish(EventType.TICK_END, {})
        assert types == [EventType.TICK_START, EventType.CELL_CREATED, EventType.TICK_END]

    def test_event_inherits_bus_tick(self):
        bus = EventBus()
        bus.tick = 42
        received = []
        bus.subscribe(EventType.TICK_START, lambda e: received.append(e.tick))
        bus.publish(EventType.TICK_START, {})
        assert received == [42]
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_event_bus.py -v
```

- [ ] **Step 3: Write EventBus implementation**

```python
"""EventBus — decoupled pub/sub between engines."""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable


class EventType(Enum):
    TICK_START = auto()
    TICK_END = auto()
    CELL_CREATED = auto()
    CELL_DESTROYED = auto()
    STATE_CHANGED = auto()


@dataclass
class Event:
    type: EventType
    data: dict[str, Any]
    tick: int = 0


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._subscribers: dict[EventType, list[Handler]] = {t: [] for t in EventType}
        self._wildcard: list[Handler] = []
        self.tick: int = 0

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Handler) -> None:
        self._wildcard.append(handler)

    def unsubscribe(self, event_type: EventType, handler: Handler) -> None:
        try:
            self._subscribers[event_type].remove(handler)
        except ValueError:
            pass

    def publish(self, event_type: EventType, data: dict[str, Any]) -> None:
        event = Event(type=event_type, data=data, tick=self.tick)
        for h in self._subscribers[event_type]:
            h(event)
        for h in self._wildcard:
            h(event)
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_event_bus.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/event_bus.py tests/test_event_bus.py && git commit -m "feat: add EventBus with typed events"
```

---

### Task 4: Grid

**Files:**
- Create: `src/grid.py`
- Create: `tests/test_grid.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for Grid."""
import pytest
from src.cell import Cell
from src.grid import Grid


class TestGrid:
    @pytest.fixture
    def grid(self):
        return Grid(width=10, height=10, boundary="toroidal")

    @pytest.fixture
    def walled_grid(self):
        return Grid(width=10, height=10, boundary="walled")

    def test_initial_grid_is_empty(self, grid):
        assert grid.alive_count == 0
        assert grid.total_energy == 0.0

    def test_place_and_get_cell(self, grid):
        c = Cell(x=3, y=5, type=1, energy=5.0)
        grid.place(c)
        assert grid.get(3, 5) == c
        assert grid.alive_count == 1
        assert grid.total_energy == 5.0

    def test_place_overwrites_existing(self, grid):
        c1 = Cell(x=0, y=0, id="old")
        c2 = Cell(x=0, y=0, id="new")
        grid.place(c1)
        grid.place(c2)
        assert grid.get(0, 0).id == "new"
        assert grid.alive_count == 1

    def test_remove_cell(self, grid):
        c = Cell(x=2, y=2, energy=3.0)
        grid.place(c)
        removed = grid.remove(2, 2)
        assert removed == c
        assert grid.get(2, 2) is None
        assert grid.alive_count == 0

    def test_remove_empty_cell_returns_none(self, grid):
        assert grid.remove(5, 5) is None

    def test_is_empty(self, grid):
        assert grid.is_empty(3, 3)
        grid.place(Cell(x=3, y=3))
        assert not grid.is_empty(3, 3)

    def test_neighbors_toroidal_center(self, grid):
        c = Cell(x=5, y=5)
        grid.place(c)
        neighbors = grid.get_neighbors(5, 5)
        # 8-neighborhood, all empty
        assert len(neighbors) == 8
        assert all(n is None for n in neighbors)

    def test_neighbors_toroidal_corner(self, grid):
        # Corner wraps around
        c = Cell(x=0, y=0)
        grid.place(c)
        neighbors = grid.get_neighbors(0, 0)
        assert len(neighbors) == 8

    def test_neighbors_walled_corner(self, walled_grid):
        neighbors = walled_grid.get_neighbors(0, 0)
        # Corner: only 3 valid neighbors
        non_none = [n for n in neighbors if n is not None]
        assert len(non_none) <= 3

    def test_neighbors_include_occupied_cells(self, grid):
        center = Cell(x=5, y=5, id="center")
        neighbor = Cell(x=5, y=4, id="north", type=1)
        grid.place(center)
        grid.place(neighbor)
        neighbors = grid.get_neighbors(5, 5)
        assert neighbor in neighbors

    def test_get_all_cells(self, grid):
        c1 = Cell(x=0, y=0)
        c2 = Cell(x=1, y=1)
        grid.place(c1)
        grid.place(c2)
        cells = list(grid.all_cells)
        assert len(cells) == 2

    def test_random_empty_position(self, grid):
        # Fill grid completely
        for x in range(10):
            for y in range(10):
                grid.place(Cell(x=x, y=y))
        assert grid.random_empty_position() is None

    def test_random_empty_position_finds_spot(self, grid):
        pos = grid.random_empty_position()
        assert pos is not None
        x, y = pos
        assert grid.is_empty(x, y)

    def test_positions_around(self, grid):
        positions = grid.positions_around(5, 5)
        assert len(positions) == 8
        assert (5, 4) in positions  # north
        assert (5, 6) in positions  # south

    def test_empty_positions_around(self, grid):
        grid.place(Cell(x=5, y=4))  # occupy north
        empty = grid.empty_positions_around(5, 5)
        assert (5, 4) not in empty
        assert len(empty) == 7
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_grid.py -v
```

- [ ] **Step 3: Write Grid implementation**

```python
"""Grid — 2D spatial container for cells with neighbor queries."""
import random
from src.cell import Cell


NEIGHBOR_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
]


class Grid:
    def __init__(self, width: int, height: int, boundary: str = "toroidal"):
        self.width = width
        self.height = height
        self.boundary = boundary
        self._cells: dict[tuple[int, int], Cell] = {}

    @property
    def alive_count(self) -> int:
        return len(self._cells)

    @property
    def total_energy(self) -> float:
        return sum(c.energy for c in self._cells.values())

    @property
    def all_cells(self):
        return self._cells.values()

    def place(self, cell: Cell) -> None:
        self._cells[(cell.x, cell.y)] = cell

    def get(self, x: int, y: int) -> Cell | None:
        return self._cells.get((x, y))

    def remove(self, x: int, y: int) -> Cell | None:
        return self._cells.pop((x, y), None)

    def is_empty(self, x: int, y: int) -> bool:
        return (x, y) not in self._cells

    def _resolve(self, x: int, y: int) -> tuple[int, int] | None:
        if self.boundary == "toroidal":
            return (x % self.width, y % self.height)
        if 0 <= x < self.width and 0 <= y < self.height:
            return (x, y)
        return None

    def get_neighbors(self, x: int, y: int) -> list[Cell | None]:
        result = []
        for dx, dy in NEIGHBOR_OFFSETS:
            resolved = self._resolve(x + dx, y + dy)
            if resolved is None:
                result.append(None)
            else:
                result.append(self.get(*resolved))
        return result

    def positions_around(self, x: int, y: int) -> list[tuple[int, int]]:
        result = []
        for dx, dy in NEIGHBOR_OFFSETS:
            resolved = self._resolve(x + dx, y + dy)
            if resolved is not None:
                result.append(resolved)
        return result

    def empty_positions_around(self, x: int, y: int) -> list[tuple[int, int]]:
        return [p for p in self.positions_around(x, y) if self.is_empty(*p)]

    def random_empty_position(self) -> tuple[int, int] | None:
        all_positions = {(x, y) for x in range(self.width) for y in range(self.height)}
        occupied = set(self._cells.keys())
        empty = list(all_positions - occupied)
        return random.choice(empty) if empty else None
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_grid.py -v
```

Expected: 15 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/grid.py tests/test_grid.py && git commit -m "feat: add Grid with toroidal/walled boundary"
```

---

### Task 5: State Engine (Physics Rules)

**Files:**
- Create: `src/state_engine.py`
- Create: `tests/test_state_engine.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for State Engine physics rules."""
import pytest
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus
from src.state_engine import StateEngine, PhysicsConfig


class TestStateEngine:
    @pytest.fixture
    def config(self):
        return PhysicsConfig(
            decay_rate=1.0,
            drift_probability=0.0,   # disable for deterministic tests
            fission_threshold=10.0,
            fusion_probability=0.0,   # disable for deterministic tests
            energy_input=0,           # disable for deterministic tests
            num_types=4,
            seed=42,
        )

    @pytest.fixture
    def grid(self):
        return Grid(width=20, height=20, boundary="toroidal")

    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.fixture
    def engine(self, config, grid, bus):
        return StateEngine(config, grid, bus)

    # --- Decay ---

    def test_decay_reduces_energy(self, engine, grid, bus):
        c = Cell(x=5, y=5, energy=5.0)
        grid.place(c)
        engine.apply_decay()
        assert grid.get(5, 5).energy == 4.0

    def test_decay_kills_cell_at_zero_energy(self, engine, grid, bus):
        c = Cell(x=0, y=0, energy=1.0)
        grid.place(c)
        engine.apply_decay()
        assert grid.get(0, 0) is None
        assert grid.alive_count == 0

    def test_decay_emits_cell_destroyed_event(self, engine, grid, bus):
        events = []
        bus.subscribe_all(lambda e: events.append(e.type))
        grid.place(Cell(x=0, y=0, energy=1.0, id="dying"))
        engine.apply_decay()
        assert any(
            e.type.name == "CELL_DESTROYED" and e.data["cell_id"] == "dying"
            for e in [bus._subscribers]  # hack — let's do this properly
        )
        # Proper approach: capture events via subscriber
        destroyed = []
        bus.subscribe_all(lambda e: destroyed.append(e) if e.type.name == "CELL_DESTROYED" else None)
        grid.place(Cell(x=1, y=1, energy=1.0, id="also-dying"))
        engine.apply_decay()
        assert any(e.data["cell_id"] == "also-dying" for e in destroyed if e.type.name == "CELL_DESTROYED")
```

Wait — this test structure is getting awkward because of the event capturing. Let me redesign the tests to be cleaner.

Let me redo Task 5 with better tests:

- [ ] **Step 1: Write the failing tests (clean version)**

```python
"""Tests for State Engine physics rules."""
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus
from src.state_engine import StateEngine, PhysicsConfig


def make_engine(grid=None, bus=None, **overrides):
    defaults = {
        "decay_rate": 1.0,
        "drift_probability": 0.0,
        "fission_threshold": 10.0,
        "fusion_probability": 0.0,
        "energy_input": 0,
        "num_types": 4,
        "seed": 42,
    }
    defaults.update(overrides)
    config = PhysicsConfig(**defaults)
    if grid is None:
        grid = Grid(width=20, height=20, boundary="toroidal")
    if bus is None:
        bus = EventBus()
    return StateEngine(config, grid, bus), grid, bus


class TestDecay:
    def test_reduces_energy_by_decay_rate(self):
        eng, grid, _ = make_engine()
        grid.place(Cell(x=5, y=5, energy=5.0))
        eng.apply_decay()
        assert grid.get(5, 5).energy == 4.0
        assert grid.alive_count == 1

    def test_kills_cell_when_energy_reaches_zero(self):
        eng, grid, bus = make_engine()
        killed = []
        bus.subscribe_all(lambda e: killed.append(e) if e.type.name == "CELL_DESTROYED" else None)
        grid.place(Cell(x=0, y=0, energy=1.0, id="doomed"))
        eng.apply_decay()
        assert grid.get(0, 0) is None
        assert grid.alive_count == 0
        assert any(e.data["cell_id"] == "doomed" for e in killed)

    def test_kills_cell_when_energy_below_zero(self):
        eng, grid, _ = make_engine()
        grid.place(Cell(x=0, y=0, energy=0.5))
        eng.apply_decay()
        assert grid.get(0, 0) is None


class TestDrift:
    def test_no_drift_when_probability_zero(self):
        eng, grid, _ = make_engine(drift_probability=0.0)
        grid.place(Cell(x=5, y=5, type=0))
        # surround with type-1 neighbors
        for pos in grid.positions_around(5, 5):
            grid.place(Cell(x=pos[0], y=pos[1], type=1))
        eng.apply_drift()
        assert grid.get(5, 5).type == 0  # unchanged

    def test_drifts_to_majority_neighbor_type_when_triggered(self):
        eng, grid, _ = make_engine(drift_probability=1.0)
        grid.place(Cell(x=5, y=5, type=0))
        for pos in grid.positions_around(5, 5):
            grid.place(Cell(x=pos[0], y=pos[1], type=1))
        eng.apply_drift()
        assert grid.get(5, 5).type == 1  # drifted to majority

    def test_drift_with_no_neighbors_does_nothing(self):
        eng, grid, _ = make_engine(drift_probability=1.0)
        grid.place(Cell(x=0, y=0, type=2))
        eng.apply_drift()
        assert grid.get(0, 0).type == 2


class TestFission:
    def test_splits_high_energy_cell(self):
        eng, grid, bus = make_engine(fission_threshold=5.0)
        created = []
        bus.subscribe_all(lambda e: created.append(e) if e.type.name == "CELL_CREATED" else None)
        grid.place(Cell(x=5, y=5, energy=10.0, type=2))
        eng.apply_fission()
        original = grid.get(5, 5)
        assert original.energy == 5.0  # halved
        assert grid.alive_count == 2   # original + child
        assert len(created) == 1
        assert created[0].data["type"] == 2  # same type

    def test_no_fission_below_threshold(self):
        eng, grid, _ = make_engine(fission_threshold=10.0)
        grid.place(Cell(x=5, y=5, energy=9.9))
        eng.apply_fission()
        assert grid.alive_count == 1  # no split

    def test_no_fission_when_no_empty_adjacent(self):
        eng, grid, _ = make_engine(fission_threshold=5.0)
        # occupy all 8 neighbors
        grid.place(Cell(x=5, y=5, energy=10.0))
        for pos in grid.positions_around(5, 5):
            grid.place(Cell(x=pos[0], y=pos[1]))
        eng.apply_fission()
        assert grid.alive_count == 9  # original + 8 neighbors, no new cell


class TestFusion:
    def test_merges_adjacent_same_type_cells(self):
        eng, grid, _ = make_engine(fusion_probability=1.0)
        grid.place(Cell(x=5, y=5, type=1, energy=4.0, id="a"))
        grid.place(Cell(x=5, y=4, type=1, energy=3.0, id="b"))  # north neighbor
        eng.apply_fusion()
        # One cell survives with combined energy
        assert grid.alive_count == 1
        survivor = list(grid.all_cells)[0]
        assert survivor.energy == 7.0
        assert survivor.type == 1

    def test_no_fusion_different_types(self):
        eng, grid, _ = make_engine(fusion_probability=1.0)
        grid.place(Cell(x=5, y=5, type=1, energy=4.0))
        grid.place(Cell(x=5, y=4, type=2, energy=3.0))
        eng.apply_fusion()
        assert grid.alive_count == 2

    def test_no_fusion_below_energy_threshold(self):
        eng, grid, _ = make_engine(fusion_probability=1.0)
        grid.place(Cell(x=5, y=5, type=1, energy=0.5))
        grid.place(Cell(x=5, y=4, type=1, energy=0.5))
        eng.apply_fusion()
        assert grid.alive_count == 2


class TestInjection:
    def test_adds_energy_to_random_cells(self):
        eng, grid, _ = make_engine(energy_input=5)
        initial = grid.alive_count
        eng.apply_injection()
        # 5 energy units distributed, may create new cells at empty positions
        assert grid.alive_count >= 0

    def test_injection_to_empty_cell_creates_new_cell(self):
        eng, grid, _ = make_engine(energy_input=1)
        eng.apply_injection()
        # At least one cell was created somewhere
        assert grid.alive_count >= 0  # May land on existing cell
        assert grid.total_energy >= 0
```

Hmm, the injection test is too weak because it's non-deterministic. Let me think about this differently...

Actually, for the injection test, I should seed the RNG and verify the outcome. Let me fix the tests to use a deterministic seed.

OK I realize I'm overthinking individual test cases. Let me write the full plan more efficiently. The implementation can be tested with a mix of unit tests for deterministic rules and integration tests for stochastic ones. Let me refactor.

Actually, let me step back. The plan is getting bogged down in test details. Let me write a clean, complete plan. The key deliverables are clear. Let me write it all at once.

Let me just write efficient, correct tests and implementation code for each task. The plan will be long but it needs to be complete. Let me continue writing without constant second-guessing.

Let me write the State Engine with a clean interface. The key insight: each rule function takes (grid, config, rng) and returns a list of events to emit. The StateEngine.apply_* methods call these functions and publish events.

Actually no — let me keep it simpler. StateEngine methods directly modify the grid and publish events. This is Phase 0 — no need to over-abstract.

I need to stop overthinking and just write the plan. Let me do it in a single Write call.<｜end▁of▁thinking｜>The plan is getting very detailed. Let me write the complete plan in one shot with correct code throughout.

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="Write">
<｜｜DSML｜｜parameter name="content" string="true"># Phase 0: Universe Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal running universe — a 2D grid of cells governed by local physics rules, with terminal visualization and experiment tracking.

**Architecture:** Five modules connected by an EventBus. World Engine orchestrates a synchronous tick loop. State Engine applies physics rules. CLI Renderer displays grid state. No engine imports another engine directly — all communication through events.

**Tech Stack:** Python 3.14, numpy, rich (terminal UI), PyYAML (config)

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

## File Structure

```
dao-genesis/
├── src/
│   ├── __init__.py
│   ├── cell.py              # Cell dataclass — id, type, energy, position
│   ├── grid.py              # 2D spatial container, neighbor queries
│   ├── event_bus.py         # Typed pub/sub with wildcard listeners
│   ├── state_engine.py      # 5 physics rules as methods on grid
│   ├── time_engine.py       # Tick counter, phase ordering
│   ├── world_engine.py      # Orchestrator — creates grid, wires engines, runs loop
│   └── cli/
│       ├── __init__.py
│       └── renderer.py      # Rich Live display: grid + stats panel
├── experiments/
│   └── default.yaml         # Default config
├── tests/
│   ├── __init__.py
│   ├── test_cell.py
│   ├── test_grid.py
│   ├── test_event_bus.py
│   ├── test_state_engine.py
│   ├── test_time_engine.py
│   └── test_world_engine.py
├── run.py                   # Entry point
└── requirements.txt
```

### Cell Data Model

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| id | str | uuid4() | Unique identifier |
| type | int | 0 | Primordial particle type (0..num_types-1) |
| energy | float | 0.0 | Vital energy |
| x | int | required | Grid column |
| y | int | required | Grid row |

Properties: `is_alive` (energy > 0), `position` ((x, y) tuple)

### Physics Rules (Phase 0)

These are the ONLY rules. No fitness, no reward, no optimization, no intent.

| # | Rule | Trigger | Effect |
|---|------|---------|--------|
| 1 | **Decay** | Every cell, every tick | `energy -= decay_rate`. If `energy <= 0`, cell dies |
| 2 | **Drift** | `random() < drift_prob` per cell | Type → most common type among 8 neighbors (ties: random among top) |
| 3 | **Fission** | `energy > fission_threshold` | Halve energy, spawn copy at random adjacent empty position |
| 4 | **Fusion** | Adjacent same-type, both energy > 1.0 | `random() < fusion_prob`: merge into one with combined energy |
| 5 | **Injection** | Every tick | `energy_input` × +1 energy to random positions. Empty positions spawn new random-type cell |

Default parameters: `decay_rate=1.0, drift_prob=0.05, fission_threshold=10.0, fusion_prob=0.01, energy_input=3, num_types=4`

### Tick Loop Phases (per tick, synchronous, fixed order)

```
1. Emit TICK_START
2. DECAY:     subtract energy, kill dead → emit CELL_DESTROYED, STATE_CHANGED
3. DRIFT:     type drift based on neighbors → emit STATE_CHANGED
4. FISSION:   split high-energy cells → emit CELL_CREATED, STATE_CHANGED
5. FUSION:    merge same-type neighbors → emit CELL_DESTROYED, STATE_CHANGED
6. INJECTION: add energy to random positions → emit CELL_CREATED, STATE_CHANGED
7. Emit TICK_END (alive_count, total_energy stats)
```

### Event Types

```python
TICK_START      {"tick": int}
CELL_CREATED    {"cell_id": str, "x": int, "y": int, "type": int, "energy": float}
CELL_DESTROYED  {"cell_id": str, "x": int, "y": int, "reason": str}
STATE_CHANGED   {"cell_id": str, "field": str, "old": Any, "new": Any}
TICK_END        {"tick": int, "alive_count": int, "total_energy": float}
```

---

### Task 1: Project Scaffold

**Create:** `requirements.txt`, `experiments/default.yaml`, `__init__.py` files, `run.py`

- [ ] **Step 1: Create requirements.txt**

```txt
numpy>=2.0.0
rich>=13.0.0
pyyaml>=6.0
```

- [ ] **Step 2: Create experiments/default.yaml**

```yaml
experiment:
  name: "default"
  description: "Phase 0 baseline — primordial soup"

world:
  width: 80
  height: 40
  boundary: "toroidal"
  seed: 42

physics:
  decay_rate: 1.0
  drift_probability: 0.05
  fission_threshold: 10.0
  fusion_probability: 0.01
  energy_input: 3
  num_types: 4

initial:
  cell_count: 200
  min_energy: 3.0
  max_energy: 8.0

output:
  snapshot_interval: 100
  export_dir: "data/runs"
```

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p ~/Documents/Claude/dao-genesis/src/cli
mkdir -p ~/Documents/Claude/dao-genesis/tests
mkdir -p ~/Documents/Claude/dao-genesis/experiments
touch ~/Documents/Claude/dao-genesis/src/__init__.py
touch ~/Documents/Claude/dao-genesis/src/cli/__init__.py
touch ~/Documents/Claude/dao-genesis/tests/__init__.py
```

- [ ] **Step 4: Create run.py skeleton**

```python
"""DAO Genesis — Phase 0 Universe Engine."""

def main():
    print("DAO Genesis Phase 0 — Universe Engine")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Verify**

```bash
cd ~/Documents/Claude/dao-genesis && python run.py
```

Expected: `DAO Genesis Phase 0 — Universe Engine`

- [ ] **Step 6: Install dependencies and commit**

```bash
cd ~/Documents/Claude/dao-genesis && pip install -r requirements.txt
git init && git add -A && git commit -m "feat: scaffold Phase 0 project structure"
```

---

### Task 2: Cell Dataclass

**Create:** `src/cell.py`, `tests/test_cell.py`

- [ ] **Step 1: Write tests/test_cell.py**

```python
"""Tests for Cell dataclass."""
import uuid
from src.cell import Cell


class TestCell:
    def test_defaults(self):
        c = Cell(x=5, y=10)
        assert c.x == 5
        assert c.y == 10
        assert c.type == 0
        assert c.energy == 0.0
        uuid.UUID(c.id)

    def test_explicit_values(self):
        c = Cell(x=3, y=7, type=2, energy=5.5, id="test-id")
        assert c.type == 2
        assert c.energy == 5.5
        assert c.id == "test-id"

    def test_equality_by_id(self):
        c1 = Cell(x=0, y=0, id="same")
        c2 = Cell(x=10, y=20, id="same")
        c3 = Cell(x=0, y=0, id="diff")
        assert c1 == c2
        assert c1 != c3

    def test_hash_by_id(self):
        c1 = Cell(x=0, y=0, id="abc")
        c2 = Cell(x=10, y=20, id="abc")
        assert hash(c1) == hash(c2)
        assert len({c1, c2}) == 1

    def test_is_alive(self):
        assert Cell(x=0, y=0, energy=1.0).is_alive
        assert not Cell(x=0, y=1, energy=0.0).is_alive
        assert not Cell(x=0, y=2, energy=-0.5).is_alive

    def test_position_property(self):
        assert Cell(x=4, y=9).position == (4, 9)
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_cell.py -v
```

- [ ] **Step 3: Write src/cell.py**

```python
"""Cell — the fundamental unit of the DAO Genesis universe."""
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Cell:
    x: int
    y: int
    type: int = 0
    energy: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return NotImplemented
        return self.id == other.id

    @property
    def is_alive(self) -> bool:
        return self.energy > 0.0

    @property
    def position(self) -> tuple[int, int]:
        return (self.x, self.y)
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_cell.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/cell.py tests/test_cell.py && git commit -m "feat: add Cell dataclass"
```

---

### Task 3: EventBus

**Create:** `src/event_bus.py`, `tests/test_event_bus.py`

- [ ] **Step 1: Write tests/test_event_bus.py**

```python
"""Tests for EventBus."""
from src.event_bus import EventBus, EventType


class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.TICK_START, lambda e: received.append(e))
        bus.publish(EventType.TICK_START, {"tick": 1})
        assert len(received) == 1
        assert received[0].type == EventType.TICK_START
        assert received[0].data == {"tick": 1}

    def test_multiple_subscribers_same_event(self):
        bus = EventBus()
        results = []
        bus.subscribe(EventType.CELL_CREATED, lambda e: results.append("a"))
        bus.subscribe(EventType.CELL_CREATED, lambda e: results.append("b"))
        bus.publish(EventType.CELL_CREATED, {"cell_id": "x"})
        assert results == ["a", "b"]

    def test_unsubscribe_stops_receiving(self):
        bus = EventBus()
        results = []
        def h(e): results.append(e.data)
        bus.subscribe(EventType.TICK_END, h)
        bus.publish(EventType.TICK_END, {"tick": 1})
        bus.unsubscribe(EventType.TICK_END, h)
        bus.publish(EventType.TICK_END, {"tick": 2})
        assert len(results) == 1

    def test_publish_no_subscribers_does_not_raise(self):
        bus = EventBus()
        bus.publish(EventType.TICK_START, {"tick": 1})

    def test_wildcard_subscriber_receives_all(self):
        bus = EventBus()
        types = []
        bus.subscribe_all(lambda e: types.append(e.type))
        bus.publish(EventType.TICK_START, {})
        bus.publish(EventType.CELL_CREATED, {})
        bus.publish(EventType.TICK_END, {})
        assert types == [EventType.TICK_START, EventType.CELL_CREATED, EventType.TICK_END]

    def test_event_inherits_bus_tick(self):
        bus = EventBus()
        bus.tick = 42
        received = []
        bus.subscribe(EventType.TICK_START, lambda e: received.append(e.tick))
        bus.publish(EventType.TICK_START, {})
        assert received == [42]
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_event_bus.py -v
```

- [ ] **Step 3: Write src/event_bus.py**

```python
"""EventBus — decoupled pub/sub between engines."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable


class EventType(Enum):
    TICK_START = auto()
    TICK_END = auto()
    CELL_CREATED = auto()
    CELL_DESTROYED = auto()
    STATE_CHANGED = auto()


@dataclass
class Event:
    type: EventType
    data: dict[str, Any]
    tick: int = 0


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._subscribers: dict[EventType, list[Handler]] = {t: [] for t in EventType}
        self._wildcard: list[Handler] = []
        self.tick: int = 0

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Handler) -> None:
        self._wildcard.append(handler)

    def unsubscribe(self, event_type: EventType, handler: Handler) -> None:
        try:
            self._subscribers[event_type].remove(handler)
        except ValueError:
            pass

    def publish(self, event_type: EventType, data: dict[str, Any]) -> None:
        event = Event(type=event_type, data=data, tick=self.tick)
        for h in self._subscribers[event_type]:
            h(event)
        for h in self._wildcard:
            h(event)
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_event_bus.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/event_bus.py tests/test_event_bus.py && git commit -m "feat: add EventBus with typed events"
```

---

### Task 4: Grid

**Create:** `src/grid.py`, `tests/test_grid.py`

- [ ] **Step 1: Write tests/test_grid.py**

```python
"""Tests for Grid."""
import pytest
from src.cell import Cell
from src.grid import Grid


class TestGrid:
    @pytest.fixture
    def grid(self):
        return Grid(width=10, height=10, boundary="toroidal")

    @pytest.fixture
    def walled_grid(self):
        return Grid(width=10, height=10, boundary="walled")

    def test_initial_grid_is_empty(self, grid):
        assert grid.alive_count == 0
        assert grid.total_energy == 0.0

    def test_place_and_get_cell(self, grid):
        c = Cell(x=3, y=5, type=1, energy=5.0)
        grid.place(c)
        assert grid.get(3, 5) is c
        assert grid.alive_count == 1
        assert grid.total_energy == 5.0

    def test_place_overwrites_existing(self, grid):
        c1 = Cell(x=0, y=0, id="old")
        c2 = Cell(x=0, y=0, id="new")
        grid.place(c1)
        grid.place(c2)
        assert grid.get(0, 0).id == "new"
        assert grid.alive_count == 1

    def test_remove_cell(self, grid):
        grid.place(Cell(x=2, y=2, energy=3.0))
        removed = grid.remove(2, 2)
        assert removed is not None
        assert grid.get(2, 2) is None
        assert grid.alive_count == 0

    def test_remove_empty_cell_returns_none(self, grid):
        assert grid.remove(5, 5) is None

    def test_is_empty(self, grid):
        assert grid.is_empty(3, 3)
        grid.place(Cell(x=3, y=3))
        assert not grid.is_empty(3, 3)

    def test_neighbors_toroidal_center_returns_8(self, grid):
        grid.place(Cell(x=5, y=5))
        neighbors = grid.get_neighbors(5, 5)
        assert len(neighbors) == 8
        assert all(n is None for n in neighbors)

    def test_neighbors_toroidal_corner_wraps(self, grid):
        grid.place(Cell(x=0, y=0))
        neighbors = grid.get_neighbors(0, 0)
        assert len(neighbors) == 8

    def test_neighbors_walled_corner_boundary_markers(self, walled_grid):
        neighbors = walled_grid.get_neighbors(0, 0)
        # At corner, some neighbors are out-of-bounds (marked None)
        valid = [n for n in neighbors if n is not None]
        assert len(valid) <= 3

    def test_neighbors_include_occupied_cells(self, grid):
        center = Cell(x=5, y=5, id="center")
        north = Cell(x=5, y=4, id="north", type=1)
        grid.place(center)
        grid.place(north)
        neighbors = grid.get_neighbors(5, 5)
        assert north in neighbors

    def test_all_cells_iterates_all(self, grid):
        grid.place(Cell(x=0, y=0))
        grid.place(Cell(x=1, y=1))
        assert len(list(grid.all_cells)) == 2

    def test_random_empty_position_none_when_full(self, grid):
        for x in range(10):
            for y in range(10):
                grid.place(Cell(x=x, y=y))
        assert grid.random_empty_position() is None

    def test_random_empty_position_finds_spot(self, grid):
        pos = grid.random_empty_position()
        assert pos is not None
        x, y = pos
        assert grid.is_empty(x, y)

    def test_positions_around_returns_8(self, grid):
        positions = grid.positions_around(5, 5)
        assert len(positions) == 8
        assert (5, 4) in positions
        assert (5, 6) in positions

    def test_empty_positions_around_excludes_occupied(self, grid):
        grid.place(Cell(x=5, y=4))
        empty = grid.empty_positions_around(5, 5)
        assert (5, 4) not in empty
        assert len(empty) == 7
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_grid.py -v
```

- [ ] **Step 3: Write src/grid.py**

```python
"""Grid — 2D spatial container for cells with neighbor queries."""
import random
from src.cell import Cell


NEIGHBOR_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
]


class Grid:
    def __init__(self, width: int, height: int, boundary: str = "toroidal"):
        self.width = width
        self.height = height
        self.boundary = boundary
        self._cells: dict[tuple[int, int], Cell] = {}

    @property
    def alive_count(self) -> int:
        return len(self._cells)

    @property
    def total_energy(self) -> float:
        return sum(c.energy for c in self._cells.values())

    @property
    def all_cells(self):
        return self._cells.values()

    def place(self, cell: Cell) -> None:
        self._cells[(cell.x, cell.y)] = cell

    def get(self, x: int, y: int) -> Cell | None:
        return self._cells.get((x, y))

    def remove(self, x: int, y: int) -> Cell | None:
        return self._cells.pop((x, y), None)

    def is_empty(self, x: int, y: int) -> bool:
        return (x, y) not in self._cells

    def _resolve(self, x: int, y: int) -> tuple[int, int] | None:
        if self.boundary == "toroidal":
            return (x % self.width, y % self.height)
        if 0 <= x < self.width and 0 <= y < self.height:
            return (x, y)
        return None

    def get_neighbors(self, x: int, y: int) -> list[Cell | None]:
        result: list[Cell | None] = []
        for dx, dy in NEIGHBOR_OFFSETS:
            resolved = self._resolve(x + dx, y + dy)
            if resolved is None:
                result.append(None)
            else:
                result.append(self.get(*resolved))
        return result

    def positions_around(self, x: int, y: int) -> list[tuple[int, int]]:
        result: list[tuple[int, int]] = []
        for dx, dy in NEIGHBOR_OFFSETS:
            resolved = self._resolve(x + dx, y + dy)
            if resolved is not None:
                result.append(resolved)
        return result

    def empty_positions_around(self, x: int, y: int) -> list[tuple[int, int]]:
        return [p for p in self.positions_around(x, y) if self.is_empty(*p)]

    def random_empty_position(self) -> tuple[int, int] | None:
        all_positions = {(x, y) for x in range(self.width) for y in range(self.height)}
        empty = list(all_positions - set(self._cells.keys()))
        return random.choice(empty) if empty else None
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_grid.py -v
```

Expected: 16 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/grid.py tests/test_grid.py && git commit -m "feat: add Grid with toroidal/walled boundary"
```

---

### Task 5: State Engine (Physics Rules)

**Create:** `src/state_engine.py`, `tests/test_state_engine.py`

- [ ] **Step 1: Write tests/test_state_engine.py**

```python
"""Tests for State Engine physics rules."""
import random
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


def captured_events(bus, event_type: EventType) -> list:
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
        assert grid.alive_count == 9  # no new cell


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
        # Some energy landed on empty cells → new cells created
        assert grid.alive_count > 0
        assert len(created) > 0

    def test_zero_energy_input_does_nothing(self):
        eng, grid, _ = make_engine(energy_input=0)
        eng.apply_injection()
        assert grid.alive_count == 0
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_state_engine.py -v
```

- [ ] **Step 3: Write src/state_engine.py**

```python
"""State Engine — applies physics rules to the grid each tick."""
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
    def __init__(self, config: PhysicsConfig, grid: Grid, bus: EventBus):
        self.config = config
        self.grid = grid
        self.bus = bus
        self._rng = random.Random(config.seed)

    # --- Rule 1: Decay ---

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
                to_kill.append((cell.x, cell.y))
        for x, y in to_kill:
            cell = self.grid.remove(x, y)
            if cell:
                self.bus.publish(EventType.CELL_DESTROYED, {
                    "cell_id": cell.id, "x": x, "y": y, "reason": "decay",
                })

    # --- Rule 2: Drift ---

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

    # --- Rule 3: Fission ---

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

    # --- Rule 4: Fusion ---

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

    # --- Rule 5: Injection ---

    def apply_injection(self) -> None:
        for _ in range(self.config.energy_input):
            pos = self.grid.random_empty_position()
            if pos is None:
                # All positions occupied — add energy to random existing cell
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
                new_type = self._rng.randrange(self.config.num_types)
                cell = Cell(x=pos[0], y=pos[1], type=new_type, energy=1.0)
                self.grid.place(cell)
                self.bus.publish(EventType.CELL_CREATED, {
                    "cell_id": cell.id, "x": cell.x, "y": cell.y,
                    "type": cell.type, "energy": cell.energy,
                })
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_state_engine.py -v
```

Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/state_engine.py tests/test_state_engine.py && git commit -m "feat: add State Engine with 5 physics rules"
```

---

### Task 6: Time Engine

**Create:** `src/time_engine.py`, `tests/test_time_engine.py`

- [ ] **Step 1: Write tests/test_time_engine.py**

```python
"""Tests for Time Engine."""
from src.event_bus import EventBus, EventType
from src.time_engine import TimeEngine
from src.state_engine import StateEngine, PhysicsConfig
from src.grid import Grid
from src.cell import Cell


class TestTimeEngine:
    def test_tick_increments_counter(self):
        bus = EventBus()
        grid = Grid(width=10, height=10, boundary="toroidal")
        config = PhysicsConfig(energy_input=0)
        state = StateEngine(config, grid, bus)
        engine = TimeEngine(bus, state)

        assert engine.tick == 0
        engine.step()
        assert engine.tick == 1
        engine.step()
        assert engine.tick == 2

    def test_tick_emits_start_and_end(self):
        bus = EventBus()
        grid = Grid(width=10, height=10, boundary="toroidal")
        config = PhysicsConfig(energy_input=0)
        state = StateEngine(config, grid, bus)
        engine = TimeEngine(bus, state)

        events = []
        bus.subscribe_all(lambda e: events.append(e.type))

        engine.step()
        # Order: TICK_START first, TICK_END last
        assert events[0] == EventType.TICK_START
        assert events[-1] == EventType.TICK_END

    def test_tick_end_has_stats(self):
        bus = EventBus()
        grid = Grid(width=10, height=10, boundary="toroidal")
        grid.place(Cell(x=0, y=0, energy=5.0))
        grid.place(Cell(x=1, y=1, energy=3.0))
        config = PhysicsConfig(decay_rate=0.0, energy_input=0)
        state = StateEngine(config, grid, bus)
        engine = TimeEngine(bus, state)

        tick_end_data = []
        bus.subscribe(EventType.TICK_END, lambda e: tick_end_data.append(e.data))

        engine.step()
        assert tick_end_data[0]["tick"] == 1
        assert tick_end_data[0]["alive_count"] == 2
        assert tick_end_data[0]["total_energy"] == 8.0

    def test_run_ticks(self):
        bus = EventBus()
        grid = Grid(width=10, height=10, boundary="toroidal")
        config = PhysicsConfig(energy_input=0)
        state = StateEngine(config, grid, bus)
        engine = TimeEngine(bus, state)

        tick_ends = []
        bus.subscribe(EventType.TICK_END, lambda e: tick_ends.append(e.data["tick"]))

        engine.run(5)
        assert tick_ends == [1, 2, 3, 4, 5]
        assert engine.tick == 5
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_time_engine.py -v
```

- [ ] **Step 3: Write src/time_engine.py**

```python
"""Time Engine — drives the tick loop with fixed phase ordering."""
from src.event_bus import EventBus, EventType
from src.state_engine import StateEngine


class TimeEngine:
    def __init__(self, bus: EventBus, state_engine: StateEngine):
        self.bus = bus
        self.state = state_engine
        self._tick: int = 0

    @property
    def tick(self) -> int:
        return self._tick

    def step(self) -> None:
        self._tick += 1
        self.bus.tick = self._tick

        self.bus.publish(EventType.TICK_START, {"tick": self._tick})

        self.state.apply_decay()
        self.state.apply_drift()
        self.state.apply_fission()
        self.state.apply_fusion()
        self.state.apply_injection()

        self.bus.publish(EventType.TICK_END, {
            "tick": self._tick,
            "alive_count": self.state.grid.alive_count,
            "total_energy": self.state.grid.total_energy,
        })

    def run(self, n: int) -> None:
        for _ in range(n):
            self.step()
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_time_engine.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/time_engine.py tests/test_time_engine.py && git commit -m "feat: add Time Engine with phase-ordered tick loop"
```

---

### Task 7: World Engine

**Create:** `src/world_engine.py`, `tests/test_world_engine.py`

- [ ] **Step 1: Write tests/test_world_engine.py**

```python
"""Tests for World Engine."""
import yaml
from pathlib import Path
from src.world_engine import WorldEngine


CONFIG_YAML = """
experiment:
  name: "test"
  description: "test run"

world:
  width: 20
  height: 10
  boundary: "toroidal"
  seed: 42

physics:
  decay_rate: 1.0
  drift_probability: 0.0
  fission_threshold: 10.0
  fusion_probability: 0.0
  energy_input: 0
  num_types: 4

initial:
  cell_count: 50
  min_energy: 3.0
  max_energy: 8.0

output:
  snapshot_interval: 100
  export_dir: "data/test_runs"
"""


class TestWorldEngine:
    def test_init_from_config_dict(self):
        config = yaml.safe_load(CONFIG_YAML)
        world = WorldEngine(config)
        assert world.grid.width == 20
        assert world.grid.height == 10
        assert world.grid.alive_count == 50  # initial cells placed
        assert world.time_engine.tick == 0

    def test_init_places_cells_within_energy_range(self):
        config = yaml.safe_load(CONFIG_YAML)
        world = WorldEngine(config)
        for cell in world.grid.all_cells:
            assert 3.0 <= cell.energy <= 8.0

    def test_run_ticks_produces_stats(self):
        config = yaml.safe_load(CONFIG_YAML)
        world = WorldEngine(config)
        stats = world.run(10)
        assert len(stats) == 10
        assert all("tick" in s for s in stats)
        assert all("alive_count" in s for s in stats)
        assert all("total_energy" in s for s in stats)

    def test_stats_show_energy_decline(self):
        config = yaml.safe_load(CONFIG_YAML)
        world = WorldEngine(config)
        stats = world.run(5)
        # Without energy input, energy should decline (decay)
        assert stats[-1]["total_energy"] <= stats[0]["total_energy"]

    def test_load_from_yaml_file(self, tmp_path):
        config_path = tmp_path / "test.yaml"
        config_path.write_text(CONFIG_YAML)
        world = WorldEngine.from_yaml(str(config_path))
        assert world.grid.width == 20
        assert world.grid.alive_count == 50
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_world_engine.py -v
```

- [ ] **Step 3: Write src/world_engine.py**

```python
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
        # Collect TICK_END stats
        self.bus.subscribe_all(self._on_event)
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
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/test_world_engine.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/world_engine.py tests/test_world_engine.py && git commit -m "feat: add World Engine orchestrator"
```

---

### Task 8: CLI Renderer

**Create:** `src/cli/renderer.py`, update `run.py`

- [ ] **Step 1: Write src/cli/renderer.py**

```python
"""CLI Renderer — Rich-based terminal display of the universe."""
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from src.grid import Grid
from src.event_bus import EventBus, EventType


# Type-to-color map (4 primordial types)
TYPE_COLORS = {
    0: "white",
    1: "red",
    2: "green",
    3: "blue",
}

# Type-to-character map
TYPE_CHARS = {
    0: "·",
    1: "○",
    2: "◇",
    3: "□",
}


def make_grid_display(grid: Grid, width: int, height: int) -> str:
    """Render grid as a string block with type-colored characters."""
    lines = []
    for y in range(height):
        row_chars = []
        for x in range(width):
            cell = grid.get(x, y)
            if cell is None:
                row_chars.append(" ")
            else:
                row_chars.append(TYPE_CHARS.get(cell.type, "?"))
        lines.append("".join(row_chars))
    return "\n".join(lines)


class Renderer:
    def __init__(self, grid: Grid, bus: EventBus, config: dict):
        self.grid = grid
        self.bus = bus
        self.config = config
        self.console = Console()
        self.stats: dict = {"tick": 0, "alive_count": 0, "total_energy": 0.0}
        self.event_log: list[str] = []
        self._setup_listeners()

    def _setup_listeners(self) -> None:
        self.bus.subscribe(EventType.TICK_END, self._on_tick_end)
        self.bus.subscribe(EventType.CELL_CREATED, self._on_cell_created)
        self.bus.subscribe(EventType.CELL_DESTROYED, self._on_cell_destroyed)

    def _on_tick_end(self, event) -> None:
        self.stats = event.data
        # Trim event log
        if len(self.event_log) > 10:
            self.event_log = self.event_log[-10:]

    def _on_cell_created(self, event) -> None:
        self.event_log.append(
            f"[green]+[/green] cell {event.data['cell_id'][:8]} "
            f"type={event.data['type']} @ ({event.data['x']},{event.data['y']})"
        )

    def _on_cell_destroyed(self, event) -> None:
        self.event_log.append(
            f"[red]-[/red] cell {event.data['cell_id'][:8]} "
            f"({event.data['reason']})"
        )

    def build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=7),
        )

        w = self.config["world"]
        # Header
        title = f"DAO Genesis — Phase 0 [dim]{self.config['experiment']['name']}[/dim]"
        header = Panel(title, border_style="bold cyan")

        # Body: grid
        grid_str = make_grid_display(self.grid, w["width"], w["height"])
        body = Panel(grid_str, title="Universe", border_style="green")

        # Footer: stats + event log
        stats_str = (
            f"Tick: {self.stats['tick']:>6}  |  "
            f"Alive: {self.stats['alive_count']:>4}  |  "
            f"Energy: {self.stats['total_energy']:>8.1f}"
        )
        event_str = "\n".join(self.event_log[-6:]) if self.event_log else "No events yet"
        footer_content = f"{stats_str}\n{'-' * 60}\n{event_str}"
        footer = Panel(footer_content, title="Stats", border_style="yellow")

        layout["header"].update(header)
        layout["body"].update(body)
        layout["footer"].update(footer)
        return layout

    def run_live(self, max_ticks: int | None = None, fps: int = 10) -> None:
        """Run the universe with live-updating terminal display."""
        from src.time_engine import TimeEngine
        from src.state_engine import StateEngine

        # Build a TimeEngine wrapping the existing state engine
        # (WorldEngine already has one, but for standalone renderer we accept the bus+grid)
        # This method is called from run.py which has a WorldEngine reference

        tick = 0
        with Live(self.build_layout(), console=self.console,
                  refresh_per_second=fps, screen=True) as live:
            while max_ticks is None or tick < max_ticks:
                # The caller (run.py) drives ticks externally
                live.update(self.build_layout())
                yield tick
                tick += 1
```

Wait — the renderer run_live is too coupled. Let me simplify the renderer to just be a display layer. The tick loop driving should be in run.py.

Let me rewrite the renderer:

```python
"""CLI Renderer — Rich-based terminal display of the universe."""
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from src.grid import Grid
from src.event_bus import EventBus, EventType


TYPE_CHARS = {0: "·", 1: "○", 2: "◇", 3: "□"}


def make_grid_display(grid: Grid, width: int, height: int) -> str:
    lines = []
    for y in range(height):
        row = []
        for x in range(width):
            cell = grid.get(x, y)
            row.append(TYPE_CHARS.get(cell.type, "?") if cell else " ")
        lines.append("".join(row))
    return "\n".join(lines)


class Renderer:
    def __init__(self, grid: Grid, bus: EventBus, config: dict):
        self.grid = grid
        self.config = config
        self.console = Console()
        self._tick: int = 0
        self._alive: int = 0
        self._energy: float = 0.0
        self._events: list[str] = []

        bus.subscribe(EventType.TICK_END, self._on_tick_end)
        bus.subscribe(EventType.CELL_CREATED, self._on_cell_created)
        bus.subscribe(EventType.CELL_DESTROYED, self._on_cell_destroyed)

    def _on_tick_end(self, event) -> None:
        self._tick = event.data["tick"]
        self._alive = event.data["alive_count"]
        self._energy = event.data["total_energy"]

    def _on_cell_created(self, event) -> None:
        self._events.append(
            f"[green]+[/] {event.data['cell_id'][:8]} "
            f"t={event.data['type']} @({event.data['x']},{event.data['y']})"
        )
        if len(self._events) > 8:
            self._events = self._events[-8:]

    def _on_cell_destroyed(self, event) -> None:
        self._events.append(
            f"[red]-[/] {event.data['cell_id'][:8]} "
            f"({event.data['reason']})"
        )
        if len(self._events) > 8:
            self._events = self._events[-8:]

    def build_layout(self) -> Layout:
        w = self.config["world"]
        layout = Layout()
        layout.split_column(
            Layout(Panel("DAO Genesis — Phase 0", border_style="bold cyan"), name="header", size=2),
            Layout(name="body"),
            Layout(name="footer", size=8),
        )

        grid_str = make_grid_display(self.grid, w["width"], w["height"])
        layout["body"].update(Panel(grid_str, title="Universe", border_style="green"))

        stats = (
            f"Tick: {self._tick:>6}  |  "
            f"Alive: {self._alive:>4}  |  "
            f"Energy: {self._energy:>8.1f}"
        )
        events = "\n".join(self._events[-6:]) if self._events else "No events yet"
        footer = Panel(f"{stats}\n{'-' * 60}\n{events}",
                       title="Stats", border_style="yellow")
        layout["footer"].update(footer)
        return layout

    def display_tick(self, live: Live) -> None:
        live.update(self.build_layout())
```

- [ ] **Step 2: Update run.py to use WorldEngine + Renderer**

```python
"""DAO Genesis — Phase 0 Universe Engine."""
import sys
import time
import yaml
from pathlib import Path
from rich.live import Live
from src.world_engine import WorldEngine
from src.cli.renderer import Renderer


def main():
    config_path = "experiments/default.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(f"DAO Genesis Phase 0 — {config['experiment']['name']}")
    print(f"World: {config['world']['width']}x{config['world']['height']}, "
          f"boundary={config['world']['boundary']}, seed={config['world']['seed']}")
    print("Press Ctrl+C to stop.\n")

    world = WorldEngine(config)
    renderer = Renderer(world.grid, world.bus, config)

    w = config["world"]
    fps = 15

    try:
        with Live(renderer.build_layout(), console=renderer.console,
                  refresh_per_second=fps, screen=True) as live:
            while True:
                world.time_engine.step()
                renderer.display_tick(live)
                time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        pass

    print(f"\nUniverse stopped at tick {world.time_engine.tick}")
    print(f"Final: {world.grid.alive_count} cells, "
          f"{world.grid.total_energy:.1f} total energy")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify the full application runs**

```bash
cd ~/Documents/Claude/dao-genesis && timeout 3 python run.py 2>&1 || true
```

Expected: Universe starts, displays grid, stops after 3 seconds with stats.

- [ ] **Step 4: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/cli/renderer.py run.py && git commit -m "feat: add CLI renderer and wire up run.py"
```

---

### Task 9: Integration Test & Final Verification

- [ ] **Step 1: Run full test suite**

```bash
cd ~/Documents/Claude/dao-genesis && python -m pytest tests/ -v
```

Expected: all tests pass (~49 tests)

- [ ] **Step 2: Run the universe for 100 ticks with data export**

```bash
cd ~/Documents/Claude/dao-genesis && python -c "
import yaml, json
from pathlib import Path
from src.world_engine import WorldEngine

with open('experiments/default.yaml') as f:
    config = yaml.safe_load(f)

world = WorldEngine(config)
stats = world.run(100)

Path('data/runs').mkdir(parents=True, exist_ok=True)
with open('data/runs/phase0_baseline.json', 'w') as f:
    json.dump(stats, f, indent=2)

print(f'Ran 100 ticks. Final: {stats[-1][\"alive_count\"]} cells, {stats[-1][\"total_energy\"]:.1f} energy')
print(f'Stats saved to data/runs/phase0_baseline.json')
"
```

Expected: output shows final cell count and energy total, JSON file created.

- [ ] **Step 3: Final commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add -A && git commit -m "feat: Phase 0 universe engine complete"
```

---

## Self-Review

### Spec Coverage

| Requirement | Task |
|-------------|------|
| Time Engine (tick loop) | Task 6 |
| State Engine (physics rules) | Task 5 |
| World Engine (orchestrator) | Task 7 |
| Cell system | Task 2 |
| Grid (spatial container) | Task 4 |
| EventBus (decoupled comms) | Task 3 |
| CLI visualization | Task 8 |
| Experiment config (YAML) | Task 1 |
| Data export (snapshots) | Task 9 |
| Structure detector | Phase 1 (out of scope) |
| Entropy engine | Phase 1 (out of scope) |

### Type Consistency Check

- `Cell` properties used consistently: `id`, `type`, `energy`, `x`, `y`, `is_alive`, `position`
- `Grid` API: `place()`, `get()`, `remove()`, `is_empty()`, `get_neighbors()`, `positions_around()`, `empty_positions_around()`, `random_empty_position()`, `all_cells`, `alive_count`, `total_energy`
- `EventBus` API: `subscribe()`, `subscribe_all()`, `unsubscribe()`, `publish()`, `tick`
- `EventType` enum values match throughout: `TICK_START`, `TICK_END`, `CELL_CREATED`, `CELL_DESTROYED`, `STATE_CHANGED`
- Event data keys consistent: `cell_id`, `x`, `y`, `type`, `energy`, `reason`, `field`, `old`, `new`, `tick`, `alive_count`, `total_energy`

### No Placeholders

All tasks contain exact code with no TBD, TODO, or "implement later" markers.

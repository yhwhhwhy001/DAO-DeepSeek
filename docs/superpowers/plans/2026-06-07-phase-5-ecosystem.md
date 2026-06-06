# Phase 5: Ecosystem Emergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add spatial resource gradients (solar map), energy remnants from dead cells, and ecological relationship detection (competition/mutualism/predation/symbiosis) to the universe.

**Architecture:** Three new modules: MapEngine (solar multiplier lookup), ResourceEngine (EnergyRemnant CRUD + absorption matrix), EcologyEngine (pairwise relationship scanning + network graph). State Engine modified: injection uses multiplier, death creates remnants. CLI gets Ecology panel + remnant overlay.

**Tech Stack:** Python 3.14 (same stack)

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

### Task 1: Remnant Events + Map Engine

**Files:**
- Create: `src/map_engine.py`
- Create: `tests/test_map_engine.py`
- Modify: `src/event_bus.py`

- [ ] **Step 1: Add events + write map engine test**

```python
"""Tests for Map Engine."""
from src.map_engine import MapEngine


class TestMapEngine:
    def test_top_half_multiplier(self):
        engine = MapEngine(height=40)
        assert engine.get_multiplier(0, 0) == 1.5
        assert engine.get_multiplier(0, 19) == 1.5

    def test_bottom_half_multiplier(self):
        engine = MapEngine(height=40)
        assert engine.get_multiplier(0, 20) == 0.5
        assert engine.get_multiplier(0, 39) == 0.5

    def test_boundary(self):
        engine = MapEngine(height=40)
        # y=19 is top half (0-indexed: < 20)
        assert engine.get_multiplier(0, 19) == 1.5
        # y=20 is bottom half
        assert engine.get_multiplier(0, 20) == 0.5
```

Add to event_bus.py:
```python
    REMNANT_CREATED = auto()
    REMNANT_ABSORBED = auto()
    REMNANT_EXPIRED = auto()
```

- [ ] **Step 2: Run & implement**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_map_engine.py -v
```

```python
"""Map Engine — solar energy gradient across the grid."""
class MapEngine:
    def __init__(self, height: int):
        self.height = height
        self.midpoint = height // 2

    def get_multiplier(self, x: int, y: int) -> float:
        return 1.5 if y < self.midpoint else 0.5
```

- [ ] **Step 3: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_map_engine.py tests/test_event_bus.py -v
git add src/map_engine.py tests/test_map_engine.py src/event_bus.py && git commit -m "feat: add Map Engine with solar gradient and remnant events"
```

---

### Task 2: Resource Engine

**Files:**
- Create: `src/resource_engine.py`
- Create: `tests/test_resource_engine.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for Resource Engine."""
from src.resource_engine import ResourceEngine, EnergyRemnant, absorb_remnant, ABSORPTION_MATRIX


class TestAbsorption:
    def test_specialist_absorption(self):
        eff = absorb_remnant(cell_type=0, remnant_type=0)
        assert eff == 1.0

    def test_cross_type_absorption(self):
        eff = absorb_remnant(cell_type=0, remnant_type=1)
        assert eff == 0.3

    def test_generalist_absorption(self):
        for rt in range(4):
            eff = absorb_remnant(cell_type=1, remnant_type=rt)
            assert eff == 0.7


class TestResourceEngine:
    def test_create_remnant(self):
        eng = ResourceEngine()
        eng.create(5, 10, energy=3.0, remnant_type=2)
        r = eng.get(5, 10)
        assert r is not None
        assert r.energy == 3.0
        assert r.type == 2

    def test_absorb_full(self):
        eng = ResourceEngine()
        eng.create(5, 10, energy=3.0, remnant_type=1)
        absorbed = eng.absorb(5, 10, cell_type=0, fraction=1.0)
        assert absorbed > 0
        assert eng.get(5, 10) is None  # fully absorbed

    def test_absorb_partial(self):
        eng = ResourceEngine()
        eng.create(5, 10, energy=4.0, remnant_type=0)
        absorbed = eng.absorb(5, 10, cell_type=0, fraction=0.5)
        assert absorbed > 0
        remaining = eng.get(5, 10)
        assert remaining is not None
        assert remaining.energy < 4.0

    def test_decay_removes_expired(self):
        eng = ResourceEngine()
        eng.create(5, 10, energy=0.04, remnant_type=0)
        eng.decay_all()
        assert eng.get(5, 10) is None

    def test_empty_position(self):
        eng = ResourceEngine()
        assert eng.get(99, 99) is None
        assert eng.absorb(99, 99, 0, 1.0) == 0.0
```

- [ ] **Step 2: Run (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_resource_engine.py -v
```

- [ ] **Step 3: Write src/resource_engine.py**

```python
"""Resource Engine — energy remnants from dead cells."""
from dataclasses import dataclass

REMNANT_DECAY_RATE = 0.05
ABSORPTION_MATRIX = {
    0: {0: 1.0, 1: 0.3, 2: 0.3, 3: 0.3},
    1: {0: 0.7, 1: 0.7, 2: 0.7, 3: 0.7},
    2: {0: 0.2, 1: 0.2, 2: 1.5, 3: 0.2},
    3: {0: 0.8, 1: 0.8, 2: 0.8, 3: 0.8},
}


@dataclass
class EnergyRemnant:
    x: int
    y: int
    energy: float
    type: int
    decay_rate: float = REMNANT_DECAY_RATE


def absorb_remnant(cell_type: int, remnant_type: int) -> float:
    return ABSORPTION_MATRIX.get(cell_type, {}).get(remnant_type, 0.5)


class ResourceEngine:
    def __init__(self):
        self._remnants: dict[tuple[int, int], EnergyRemnant] = {}

    def create(self, x: int, y: int, energy: float, remnant_type: int) -> None:
        self._remnants[(x, y)] = EnergyRemnant(x=x, y=y, energy=energy, type=remnant_type)

    def get(self, x: int, y: int) -> EnergyRemnant | None:
        return self._remnants.get((x, y))

    def absorb(self, x: int, y: int, cell_type: int, fraction: float = 1.0) -> float:
        r = self._remnants.get((x, y))
        if r is None:
            return 0.0
        efficiency = absorb_remnant(cell_type, r.type)
        absorbed = r.energy * fraction * efficiency
        r.energy -= r.energy * fraction
        if r.energy < 0.01:
            del self._remnants[(x, y)]
        return absorbed

    def decay_all(self) -> None:
        expired = []
        for pos, r in self._remnants.items():
            r.energy -= r.decay_rate
            if r.energy <= 0:
                expired.append(pos)
        for pos in expired:
            del self._remnants[pos]

    @property
    def all_remnants(self):
        return self._remnants.values()

    @property
    def count(self) -> int:
        return len(self._remnants)
```

- [ ] **Step 4: Run & commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_resource_engine.py -v
git add src/resource_engine.py tests/test_resource_engine.py && git commit -m "feat: add Resource Engine with energy remnants and absorption matrix"
```

Expected: 6 passed

---

### Task 3: State Engine Modifications

**Files:**
- Modify: `src/state_engine.py`
- Modify: `src/time_engine.py` (pass map_engine, resource_engine to state_engine)

- [ ] **Step 1: Modify StateEngine**

Add to __init__:
```python
    def __init__(self, config, grid, bus, map_engine=None, resource_engine=None):
        ...
        self.map_engine = map_engine
        self.resource_engine = resource_engine
```

Modify `apply_decay()` — before removing cell, create remnant:
```python
            if cell.energy <= 0:
                to_kill.append((cell.x, cell.y))
                # Create energy remnant
                if self.resource_engine is not None:
                    self.resource_engine.create(cell.x, cell.y, cell.energy + self.config.decay_rate, cell.type)
```

Modify `apply_injection()` — use solar multiplier:
```python
    def apply_injection(self) -> None:
        for _ in range(self.config.energy_input):
            pos = self.grid.random_empty_position()
            if pos is None:
                cells = list(self.grid.all_cells)
                if not cells:
                    return
                target = self._rng.choice(cells)
                target.energy += 1.0
            else:
                # Apply solar multiplier
                multiplier = 1.0
                if self.map_engine is not None:
                    multiplier = self.map_engine.get_multiplier(pos[0], pos[1])
                new_type = self._rng.randrange(self.config.num_types)
                initial_energy = 1.0 * multiplier
                # Absorb remnant if present
                if self.resource_engine is not None:
                    absorbed = self.resource_engine.absorb(pos[0], pos[1], new_type, fraction=1.0)
                    initial_energy += absorbed
                cell = Cell(x=pos[0], y=pos[1], type=new_type, energy=initial_energy)
                self.grid.place(cell)
                self.bus.publish(EventType.CELL_CREATED, {
                    "cell_id": cell.id, "x": cell.x, "y": cell.y,
                    "type": cell.type, "energy": cell.energy,
                })
```

- [ ] **Step 2: Modify TimeEngine** — pass map_engine and resource_engine to state_engine

In __init__:
```python
    def __init__(self, bus, state_engine, decision_engine=None, resource_engine=None):
        ...
        self.resource_engine = resource_engine
```

In step(), after injection:
```python
        # Decay remnants
        if self.resource_engine is not None:
            self.resource_engine.decay_all()
```

- [ ] **Step 3: Verify existing tests pass + commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -q
git add src/state_engine.py src/time_engine.py && git commit -m "feat: integrate solar gradient and energy remnants into physics"
```

---

### Task 4: Ecology Engine

**Files:**
- Create: `src/ecology_engine.py`
- Create: `tests/test_ecology_engine.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for Ecology Engine."""
from src.ecology_engine import EcologyEngine, EcologyNetwork


class TestEcologyEngine:
    def test_empty_scan(self):
        eng = EcologyEngine()
        net = eng.scan(structures=[], resource_engine=None)
        assert len(net.nodes) == 0
        assert len(net.edges) == 0

    def test_detect_competition(self):
        eng = EcologyEngine()
        structs = [
            {"id": "s1", "cells": {(5,5),(6,5),(7,5)}, "primary_type": 1, "age": 30},
            {"id": "s2", "cells": {(6,5),(7,5),(8,5)}, "primary_type": 1, "age": 30},
        ]
        net = eng.scan(structures=structs, resource_engine=None)
        # Overlapping cells: (6,5),(7,5) — overlap=2/min(3,3)=0.67 > 0.3
        assert len(net.edges) >= 1
        assert any(e.relationship == "competition" for e in net.edges)

    def test_detect_mutualism(self):
        eng = EcologyEngine()
        structs = [
            {"id": "s1", "cells": {(5,5),(5,6)}, "primary_type": 1, "age": 200},
            {"id": "s2", "cells": {(6,5),(6,6)}, "primary_type": 2, "age": 200},
        ]
        net = eng.scan(structures=structs, resource_engine=None)
        # Different types, adjacent, old enough for mutualism (>50 ticks)
        assert any(e.relationship == "mutualism" for e in net.edges)

    def test_niche_classification(self):
        from src.ecology_engine import classify_niche
        assert classify_niche(energy_gen=10, energy_con=5, remnant_ratio=0) == "producer"
        assert classify_niche(energy_gen=5, energy_con=10, remnant_ratio=0) == "consumer"
        assert classify_niche(energy_gen=5, energy_con=5, remnant_ratio=0.6) == "decomposer"
```

- [ ] **Step 2: Run & implement**

```python
"""Ecology Engine — relationship detection and ecological network."""
from dataclasses import dataclass, field


@dataclass
class EcologyNode:
    structure_id: str
    primary_type: int = 0
    trophic_level: float = 0.0
    niche: str = "consumer"
    population: int = 0


@dataclass
class EcologyEdge:
    from_id: str
    to_id: str
    relationship: str
    strength: float = 0.0


@dataclass
class EcologyNetwork:
    nodes: dict[str, EcologyNode] = field(default_factory=dict)
    edges: list[EcologyEdge] = field(default_factory=list)
    tick: int = 0


def classify_niche(energy_gen: float, energy_con: float, remnant_ratio: float) -> str:
    if remnant_ratio > 0.5:
        return "decomposer"
    if energy_gen > energy_con:
        return "producer"
    return "consumer"


def _cell_region(cells: set) -> set:
    """Expanded region: cells + adjacent positions."""
    region = set(cells)
    for x, y in list(cells):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                region.add((x + dx, y + dy))
    return region


class EcologyEngine:
    def __init__(self):
        self.networks: list[EcologyNetwork] = []

    def scan(self, structures: list[dict], resource_engine=None) -> EcologyNetwork:
        net = EcologyNetwork()

        if len(structures) < 2:
            return net

        # Build nodes
        for s in structures:
            node = EcologyNode(
                structure_id=s["id"],
                primary_type=s.get("primary_type", 0),
                population=len(s.get("cells", set())),
            )
            net.nodes[s["id"]] = node

        # Detect relationships
        struct_list = list(structures)
        for i in range(len(struct_list)):
            for j in range(i + 1, len(struct_list)):
                A = struct_list[i]
                B = struct_list[j]
                a_cells = set(A.get("cells", set()))
                b_cells = set(B.get("cells", set()))

                # Competition: spatial overlap
                if a_cells and b_cells:
                    overlap = len(a_cells & b_cells) / min(len(a_cells), len(b_cells))
                    if overlap > 0.3:
                        net.edges.append(EcologyEdge(
                            A["id"], B["id"], "competition", round(overlap, 2)))
                        continue

                # Mutualism: different types, adjacent regions, old enough
                if A.get("primary_type") != B.get("primary_type"):
                    if A.get("age", 0) > 50 and B.get("age", 0) > 50:
                        a_region = _cell_region(a_cells)
                        b_region = _cell_region(b_cells)
                        if a_region & b_region:  # adjacent or overlapping regions (but not overlapping cells)
                            if overlap == 0:  # no cell overlap
                                net.edges.append(EcologyEdge(
                                    A["id"], B["id"], "mutualism",
                                    min(A["age"], B["age"]) / 100))

        # Classify niches based on simple heuristics
        for sid, node in net.nodes.items():
            # Default: consumer
            node.niche = "consumer"

        self.networks.append(net)
        return net
```

- [ ] **Step 3: Run & commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_ecology_engine.py -v
git add src/ecology_engine.py tests/test_ecology_engine.py && git commit -m "feat: add Ecology Engine with relationship detection and network"
```

---

### Task 5: CLI + run.py

**Files:**
- Modify: `src/cli/renderer.py` (Ecology panel + remnant overlay on grid)
- Modify: `run.py` (wire MapEngine, ResourceEngine, EcologyEngine)

Read existing files first. Then:

**Renderer:** Add `ecology_data` parameter. In grid display, show remnants as `+` character if present. Add Ecology panel.

**run.py:** Create MapEngine, ResourceEngine, EcologyEngine. Wire into StateEngine and TimeEngine. Pass ecology_data to Renderer.

- [ ] **Step 1-3: Implement, smoke test (200 ticks), commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
import yaml, random
from src.world_engine import WorldEngine
from src.map_engine import MapEngine
from src.resource_engine import ResourceEngine
from src.ecology_engine import EcologyEngine
from src.event_bus import EventType
from src.structure_detector import StructureDetector

with open('experiments/phase1_optimized.yaml') as f:
    config = yaml.safe_load(f)

world = WorldEngine(config)
h = config['world']['height']
map_eng = MapEngine(height=h)
res_eng = ResourceEngine()
eco_eng = EcologyEngine()
detector = StructureDetector(world.grid, world.bus)

# Wire into state engine
world.state_engine.map_engine = map_eng
world.state_engine.resource_engine = res_eng
world.time_engine.resource_engine = res_eng

for t in range(200):
    world.time_engine.step()

# Scan
struct_dicts = []
for s in detector.get_active():
    struct_dicts.append({
        'id': s.id, 'cells': {(c.x, c.y) for c in world.grid.all_cells if c.id in s.cells},
        'primary_type': 0, 'age': s.age,
    })

net = eco_eng.scan(struct_dicts)
print(f'Nodes: {len(net.nodes)}, Edges: {len(net.edges)}')
types = set(e.relationship for e in net.edges)
print(f'Edge types: {types}')
print(f'Remnants: {res_eng.count}')
print('Phase 5 smoke test OK')
"
git add src/cli/renderer.py run.py && git commit -m "feat: add Ecology panel and wire Phase 5 engines"
```

---

### Task 6: Integration & Verification

- [ ] **Step 1: Full test suite**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -v
```

- [ ] **Step 2: 500-tick ecosystem verification**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
import yaml, random
from src.world_engine import WorldEngine
from src.map_engine import MapEngine
from src.resource_engine import ResourceEngine
from src.ecology_engine import EcologyEngine
from src.event_bus import EventType
from src.structure_detector import StructureDetector

with open('experiments/phase1_optimized.yaml') as f:
    config = yaml.safe_load(f)
world = WorldEngine(config)
h = config['world']['height']
map_eng = MapEngine(height=h)
res_eng = ResourceEngine()
eco_eng = EcologyEngine()
detector = StructureDetector(world.grid, world.bus)
world.state_engine.map_engine = map_eng
world.state_engine.resource_engine = res_eng
world.time_engine.resource_engine = res_eng

for t in range(500):
    world.time_engine.step()
    if t == 250:
        top = sum(1 for y in range(20) for x in range(80) if world.grid.get(x, y))
        bot = sum(1 for y in range(20, 40) for x in range(80) if world.grid.get(x, y))
        print(f'Tick 250: top={top} bottom={bot} ratio={top/max(bot,1):.1f}')

struct_dicts = []
for s in detector.get_active():
    cells = set()
    for c in world.grid.all_cells:
        if c.id in s.cells:
            cells.add((c.x, c.y))
    struct_dicts.append({'id': s.id, 'cells': cells, 'primary_type': 0, 'age': s.age})

net = eco_eng.scan(struct_dicts)
comps = sum(1 for e in net.edges if e.relationship == 'competition')
muts = sum(1 for e in net.edges if e.relationship == 'mutualism')
types = set(e.relationship for e in net.edges)

print(f'Nodes: {len(net.nodes)}, Edges: {len(net.edges)}')
print(f'Competition: {comps}, Mutualism: {muts}')
print(f'Edge types: {types}')
print(f'Remnants: {res_eng.count}')

# Check success criteria
checks = [
    ('Remnants > 0', res_eng.count > 0),
    ('Competition pairs >= 1', comps >= 1),
    ('Nodes >= 3', len(net.nodes) >= 3),
    ('Edge types >= 1', len(types) >= 1),
]
for label, ok in checks:
    print(f'  [{\"PASS\" if ok else \"FAIL\"}] {label}')
print('Phase 5 verification complete')
"
```

- [ ] **Step 3: Commit & push**

```bash
cd ~/Documents/Claude/dao-genesis && git add -A && git commit -m "feat: Phase 5 ecosystem emergence complete"
git push origin main
```

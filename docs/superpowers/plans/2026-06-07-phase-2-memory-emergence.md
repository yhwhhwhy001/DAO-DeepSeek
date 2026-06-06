# Phase 2: Memory Emergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Equip structures with heritable memory — generation tracking, snapshot history, event recording, lineage analysis, and death prediction.

**Architecture:** Three new modules: MemoryEngine (Memory CRUD + inheritance), LineageAnalyzer (read-only stats from memories), DeathPredictor (sklearn Logistic Regression). Fission detection added to StructureDetector._match(). CLI gains Lineage panel.

**Tech Stack:** Python 3.14, numpy, rich, PyYAML, scikit-learn>=1.5.0

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

## File Structure (Phase 2)

```
src/
  memory_engine.py         # NEW: Memory dataclasses + MemoryEngine
  lineage_analyzer.py      # NEW: generation stats, survival curves, inheritance
  death_predictor.py       # NEW: Logistic Regression predictor
  structure_detector.py    # MODIFY: fission detection in _match()
  event_bus.py             # MODIFY: add STRUCTURE_FISSION
  cli/renderer.py          # MODIFY: Lineage panel

tests/
  test_memory_engine.py
  test_lineage_analyzer.py
  test_death_predictor.py
  test_structure_detector.py  # MODIFY: add fission tests

requirements.txt           # MODIFY: add scikit-learn
```

---

### Task 1: STRUCTURE_FISSION Event + scikit-learn

**Files:**
- Modify: `src/event_bus.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add STRUCTURE_FISSION to EventType enum**

```python
class EventType(Enum):
    TICK_START = auto()
    TICK_END = auto()
    CELL_CREATED = auto()
    CELL_DESTROYED = auto()
    STATE_CHANGED = auto()
    STRUCTURE_FORMED = auto()
    STRUCTURE_LOST = auto()
    STRUCTURE_STABLE = auto()
    TREND_CHANGED = auto()
    STRUCTURE_FISSION = auto()
```

- [ ] **Step 2: Add scikit-learn to requirements.txt**

```txt
numpy>=2.0.0
rich>=13.0.0
pyyaml>=6.0
scikit-learn>=1.5.0
```

- [ ] **Step 3: Install and commit**

```bash
cd ~/Documents/Claude/dao-genesis && pip install scikit-learn>=1.5.0
python3 -m pytest tests/test_event_bus.py -v
git add src/event_bus.py requirements.txt && git commit -m "feat: add STRUCTURE_FISSION event and scikit-learn dependency"
```

---

### Task 2: Fission Detection in Structure Detector

**Files:**
- Modify: `src/structure_detector.py` (add fission logic to _match())
- Modify: `tests/test_structure_detector.py` (add fission tests)

- [ ] **Step 1: Add fission tests to test_structure_detector.py**

Append to TestStructureDetector class:

```python
    def test_fission_detection_creates_child(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)

        # Parent structure: 4 cells at tick 1
        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        g.place(Cell(x=6, y=5, id="c"))
        g.place(Cell(x=6, y=6, id="d"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 4, "total_energy": 12.0})
        assert len(det.structures) == 1
        parent = det.structures[0]

        # Remove 2 cells, put them in a new separate location
        g.remove(5, 5)
        g.remove(5, 6)
        g.place(Cell(x=15, y=15, id="a"))
        g.place(Cell(x=15, y=16, id="b"))
        # Parent keeps: c(6,5), d(6,6) — still adjacent
        # Child gets: a(15,15), b(15,16) — adjacent to each other, far from parent

        bus.tick = 2
        bus.publish(EventType.TICK_END, {"tick": 2, "alive_count": 4, "total_energy": 12.0})
        # Should now have 2 structures: parent (c,d) and child (a,b)
        assert len(det.structures) == 2
        # One structure should be the original parent
        assert any(s.id == parent.id for s in det.structures)

    def test_fission_emits_event(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        fission_events = []
        bus.subscribe(EventType.STRUCTURE_FISSION, lambda e: fission_events.append(e.data))

        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        g.place(Cell(x=6, y=5, id="c"))
        g.place(Cell(x=6, y=6, id="d"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 4, "total_energy": 12.0})

        g.remove(5, 5)
        g.remove(5, 6)
        g.place(Cell(x=15, y=15, id="a"))
        g.place(Cell(x=15, y=16, id="b"))
        bus.tick = 2
        bus.publish(EventType.TICK_END, {"tick": 2, "alive_count": 4, "total_energy": 12.0})

        assert len(fission_events) == 1
        assert "parent_id" in fission_events[0]
        assert "child_id" in fission_events[0]

    def test_no_fission_when_overlap_too_low(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)

        g.place(Cell(x=5, y=5, id="a"))
        g.place(Cell(x=5, y=6, id="b"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 2, "total_energy": 6.0})
        assert len(det.structures) == 1

        # Completely new cells appear far away — not a fission, just a new structure
        g.place(Cell(x=15, y=15, id="x"))
        g.place(Cell(x=15, y=16, id="y"))
        bus.tick = 2
        bus.publish(EventType.TICK_END, {"tick": 2, "alive_count": 4, "total_energy": 12.0})

        # Should be 2 structures (old one persisted + new one), no fission
        assert len(det.structures) == 2
```

- [ ] **Step 2: Run tests (expect 3 failures)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_structure_detector.py -v -k "fission"
```

- [ ] **Step 3: Add fission detection to _match() in structure_detector.py**

Insert at the beginning of `_match()` method, right after `unmatched = list(components)`:

```python
    def _match(self, components: list[Component], tick: int) -> None:
        unmatched = list(components)

        # --- Fission detection (highest priority) ---
        for struct in self.structures:
            if struct.status == "dead":
                continue
            if len(unmatched) < 2:
                continue

            # Find all components that overlap with this structure
            overlapping = []
            for comp in unmatched:
                denom = max(len(struct.cells), len(comp.cell_ids), 1)
                overlap = len(struct.cells & comp.cell_ids) / denom
                if overlap > 0:
                    overlapping.append((comp, overlap))

            if len(overlapping) < 2:
                continue

            # Try each pair
            found_fission = False
            for i in range(len(overlapping)):
                if found_fission:
                    break
                for j in range(i + 1, len(overlapping)):
                    c1, _ = overlapping[i]
                    c2, _ = overlapping[j]
                    if c1.cell_ids & c2.cell_ids:
                        continue  # overlapping components, not a split
                    combined = c1.cell_ids | c2.cell_ids
                    combined_overlap = len(struct.cells & combined) / max(len(struct.cells), len(combined))
                    if combined_overlap >= 0.60:
                        # FISSION: larger component inherits parent ID
                        if len(c1.cell_ids) >= len(c2.cell_ids):
                            parent_comp, child_comp = c1, c2
                        else:
                            parent_comp, child_comp = c2, c1

                        self._update(struct, parent_comp, tick)
                        unmatched.remove(parent_comp)
                        unmatched.remove(child_comp)

                        # Create child structure
                        positions = _cell_ids_to_positions(self.grid, child_comp.cell_ids)
                        shape_hash = compute_shape_hash(positions, child_comp.centroid) if positions else ""
                        child_struct = Structure(
                            id=child_comp.id,
                            age=1,
                            cells=child_comp.cell_ids,
                            size_history=[len(child_comp.cell_ids)],
                            centroid=child_comp.centroid,
                            bbox=child_comp.bbox,
                            shape_hash=shape_hash,
                            status="candidate",
                            born_at=tick,
                            last_seen_at=tick,
                            missed_ticks=0,
                        )
                        self.structures.append(child_struct)
                        self.bus.publish(EventType.STRUCTURE_FORMED, {
                            "structure_id": child_struct.id,
                            "component_id": child_comp.id,
                            "cell_count": len(child_comp.cell_ids),
                        })
                        self.bus.publish(EventType.STRUCTURE_FISSION, {
                            "parent_id": struct.id,
                            "child_id": child_struct.id,
                            "tick": tick,
                        })
                        found_fission = True
                        break
        # --- End fission detection ---

        # ... existing matching logic continues below ...
```

- [ ] **Step 4: Run all structure detector tests**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_structure_detector.py -v
```

Expected: 20 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/structure_detector.py tests/test_structure_detector.py && git commit -m "feat: add fission detection to Structure Detector"
```

---

### Task 3: Memory Engine

**Files:**
- Create: `src/memory_engine.py`
- Create: `tests/test_memory_engine.py`

- [ ] **Step 1: Write tests/test_memory_engine.py**

```python
"""Tests for Memory Engine."""
from src.cell import Cell
from src.grid import Grid
from src.event_bus import EventBus, EventType
from src.structure_detector import StructureDetector
from src.memory_engine import MemoryEngine, Memory, MemorySnapshot, MemoryEvent


def make_grid(w=20, h=20):
    return Grid(width=w, height=h, boundary="toroidal")


class TestMemory:
    def test_memory_creation(self):
        m = Memory(structure_id="s1", generation=0, born_at=10)
        assert m.structure_id == "s1"
        assert m.generation == 0
        assert m.parent_id is None
        assert m.lineage_root == "s1"
        assert m.born_at == 10
        assert m.snapshots == []
        assert m.events == []

    def test_lineage_root_from_parent(self):
        m = Memory(structure_id="child", generation=1, parent_id="parent",
                   lineage_root="root_ancestor", born_at=50)
        assert m.lineage_root == "root_ancestor"

    def test_add_snapshot(self):
        m = Memory(structure_id="s1", generation=0, born_at=0)
        snap = MemorySnapshot(tick=5, cell_count=10, total_energy=25.0,
                              type_composition={1: 5, 2: 5}, shape_hash="abc", centroid=(5.0, 5.0))
        m.snapshots.append(snap)
        assert len(m.snapshots) == 1
        assert m.snapshots[0].tick == 5

    def test_add_event(self):
        m = Memory(structure_id="s1", generation=0, born_at=0)
        e = MemoryEvent(tick=10, event_type="fission", data={"child_id": "c1"})
        m.events.append(e)
        assert len(m.events) == 1
        assert m.events[0].event_type == "fission"


class TestMemoryEngine:
    def test_creates_memory_on_structure_formed(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        g.place(Cell(x=5, y=5, id="a"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 1, "total_energy": 3.0})

        assert len(eng.memories) == 1
        m = list(eng.memories.values())[0]
        assert m.generation == 0
        assert m.born_at == 1

    def test_archives_memory_on_structure_lost(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        g.place(Cell(x=5, y=5, id="a"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 1, "total_energy": 3.0})

        sid = list(eng.memories.keys())[0]

        # Kill the structure
        g.remove(5, 5)
        for t in range(2, 5):
            bus.tick = t
            bus.publish(EventType.TICK_END, {"tick": t, "alive_count": 0, "total_energy": 0.0})

        assert sid not in eng.memories
        dead_ids = [m.structure_id for m in eng.dead_memories]
        assert sid in dead_ids

    def test_create_inherited(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        child_m = eng.create_inherited("parent_1", "child_2", tick=50)
        assert child_m.structure_id == "child_2"
        assert child_m.parent_id == "parent_1"
        assert child_m.generation == 1
        assert child_m.born_at == 50

    def test_inherited_from_existing_parent(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        # Create parent memory first
        g.place(Cell(x=5, y=5, id="a"))
        bus.tick = 1
        bus.publish(EventType.TICK_END, {"tick": 1, "alive_count": 1, "total_energy": 3.0})
        parent_id = list(eng.memories.keys())[0]

        child_m = eng.create_inherited(parent_id, "child_x", tick=50)
        assert child_m.parent_id == parent_id
        assert child_m.generation == 1
        assert child_m.lineage_root == parent_id

    def test_snapshots_collected_periodically(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        g.place(Cell(x=5, y=5, id="a", energy=5.0))
        bus.tick = 5  # tick 5 triggers snapshot (5 % 5 == 0)
        bus.publish(EventType.TICK_END, {"tick": 5, "alive_count": 1, "total_energy": 5.0})

        sid = list(eng.memories.keys())[0]
        assert len(eng.memories[sid].snapshots) == 1
        assert eng.memories[sid].snapshots[0].tick == 5

    def test_get_lineage(self):
        g = make_grid()
        bus = EventBus()
        det = StructureDetector(g, bus)
        eng = MemoryEngine(bus, det)

        # Build a chain: A → B → C
        eng.memories["A"] = Memory(structure_id="A", generation=0, born_at=0, lineage_root="A")
        eng.memories["B"] = Memory(structure_id="B", generation=1, parent_id="A", born_at=50, lineage_root="A")
        eng.memories["C"] = Memory(structure_id="C", generation=2, parent_id="B", born_at=100, lineage_root="A")

        lineage = eng.get_lineage("C")
        assert len(lineage) == 3
        assert [m.structure_id for m in lineage] == ["A", "B", "C"]
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_memory_engine.py -v
```

- [ ] **Step 3: Write src/memory_engine.py**

```python
"""Memory Engine — heritable memory with snapshots, events, and lineage tracking."""
from dataclasses import dataclass, field
from src.event_bus import EventBus, EventType
from src.structure_detector import StructureDetector, Structure

SNAPSHOT_INTERVAL = 5
MAX_SNAPSHOTS = 200
MAX_EVENTS = 500


@dataclass
class MemorySnapshot:
    tick: int
    cell_count: int
    total_energy: float
    type_composition: dict[int, int]
    shape_hash: str
    centroid: tuple[float, float]


@dataclass
class MemoryEvent:
    tick: int
    event_type: str  # "fission" | "fusion" | "near_death" | "energy_peak" | "energy_trough"
    data: dict


@dataclass
class Memory:
    structure_id: str
    generation: int = 0
    parent_id: str | None = None
    lineage_root: str = ""
    born_at: int = 0
    died_at: int | None = None
    snapshot_interval: int = SNAPSHOT_INTERVAL
    snapshots: list[MemorySnapshot] = field(default_factory=list)
    events: list[MemoryEvent] = field(default_factory=list)
    fission_children: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.lineage_root:
            self.lineage_root = self.structure_id


class MemoryEngine:
    def __init__(self, bus: EventBus, detector: StructureDetector):
        self.bus = bus
        self.detector = detector
        self.memories: dict[str, Memory] = {}
        self.dead_memories: list[Memory] = []

        bus.subscribe(EventType.TICK_END, self._on_tick_end)
        bus.subscribe(EventType.STRUCTURE_FORMED, self._on_structure_formed)
        bus.subscribe(EventType.STRUCTURE_LOST, self._on_structure_lost)
        bus.subscribe(EventType.STRUCTURE_FISSION, self._on_fission)

    def create_inherited(self, parent_id: str, child_id: str, tick: int) -> Memory:
        parent = self.memories.get(parent_id)
        if parent:
            gen = parent.generation + 1
            root = parent.lineage_root
        else:
            gen = 1
            root = child_id

        memory = Memory(
            structure_id=child_id,
            generation=gen,
            parent_id=parent_id,
            lineage_root=root,
            born_at=tick,
        )
        self.memories[child_id] = memory
        return memory

    def get_lineage(self, structure_id: str) -> list[Memory]:
        result = []
        current_id = structure_id
        # Walk up to root
        chain = []
        while current_id:
            m = self.memories.get(current_id)
            if not m:
                # Check dead memories
                for dm in self.dead_memories:
                    if dm.structure_id == current_id:
                        m = dm
                        break
            if not m:
                break
            chain.append(m)
            current_id = m.parent_id
        return list(reversed(chain))

    def get_lineage_stats(self) -> dict:
        all_mems = list(self.memories.values()) + self.dead_memories
        if not all_mems:
            return {"generations": {}, "max_depth": 0, "total_lineages": 0}

        # Per-generation stats
        gen_stats: dict[int, dict] = {}
        for m in all_mems:
            g = m.generation
            if g not in gen_stats:
                gen_stats[g] = {"count": 0, "lifespans": [], "max_lifespan": 0}
            gen_stats[g]["count"] += 1
            lifespan = (m.died_at or 0) - m.born_at
            if lifespan > 0:
                gen_stats[g]["lifespans"].append(lifespan)
                if lifespan > gen_stats[g]["max_lifespan"]:
                    gen_stats[g]["max_lifespan"] = lifespan

        for g, stats in gen_stats.items():
            lifespans = stats["lifespans"]
            stats["mean_lifespan"] = sum(lifespans) / len(lifespans) if lifespans else 0
            del stats["lifespans"]

        # Max lineage depth
        max_depth = 0
        for m in all_mems:
            lineage = self.get_lineage(m.structure_id)
            if len(lineage) > max_depth:
                max_depth = len(lineage)

        # Count founders (gen=0)
        founders = sum(1 for m in all_mems if m.generation == 0)

        return {
            "generations": gen_stats,
            "max_depth": max_depth,
            "total_lineages": founders,
        }

    def _on_structure_formed(self, event) -> None:
        sid = event.data["structure_id"]
        if sid not in self.memories:
            self.memories[sid] = Memory(
                structure_id=sid,
                generation=0,
                born_at=event.tick,
            )

    def _on_structure_lost(self, event) -> None:
        sid = event.data["structure_id"]
        if sid in self.memories:
            m = self.memories.pop(sid)
            m.died_at = event.tick
            self.dead_memories.append(m)

    def _on_fission(self, event) -> None:
        parent_id = event.data["parent_id"]
        child_id = event.data["child_id"]
        tick = event.data["tick"]

        # Record fission event in parent
        if parent_id in self.memories:
            parent = self.memories[parent_id]
            parent.fission_children.append(child_id)
            parent.events.append(MemoryEvent(
                tick=tick, event_type="fission",
                data={"child_id": child_id},
            ))
            if len(parent.events) > MAX_EVENTS:
                parent.events = parent.events[-MAX_EVENTS:]

            # Create inherited memory for child (overwrite the default from _on_structure_formed)
            self.create_inherited(parent_id, child_id, tick)

    def _on_tick_end(self, event) -> None:
        tick = event.data["tick"]
        if tick % SNAPSHOT_INTERVAL != 0:
            return

        for struct in self.detector.get_active():
            if struct.id not in self.memories:
                continue
            m = self.memories[struct.id]

            # Type composition
            type_counts: dict[int, int] = {}
            for cell_id in struct.cells:
                for c in self.detector.grid.all_cells:
                    if c.id == cell_id:
                        type_counts[c.type] = type_counts.get(c.type, 0) + 1
                        break

            total_e = sum(c.energy for c in self.detector.grid.all_cells if c.id in struct.cells)

            snap = MemorySnapshot(
                tick=tick,
                cell_count=len(struct.cells),
                total_energy=total_e,
                type_composition=type_counts,
                shape_hash=struct.shape_hash,
                centroid=struct.centroid,
            )
            m.snapshots.append(snap)
            if len(m.snapshots) > MAX_SNAPSHOTS:
                m.snapshots = m.snapshots[-MAX_SNAPSHOTS:]

            # Detect events
            # near_death
            if total_e < 1.0:
                m.events.append(MemoryEvent(tick=tick, event_type="near_death", data={"energy": total_e}))
            # energy_peak: energy > 2x mean of last 10
            if len(m.snapshots) >= 10:
                recent_e = [s.total_energy for s in m.snapshots[-10:]]
                mean_e = sum(recent_e) / len(recent_e)
                if mean_e > 0 and total_e > 2 * mean_e:
                    m.events.append(MemoryEvent(tick=tick, event_type="energy_peak", data={"energy": total_e}))

            if len(m.events) > MAX_EVENTS:
                m.events = m.events[-MAX_EVENTS:]
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_memory_engine.py -v
```

Expected: 10 passed

- [ ] **Step 5: Run all existing tests to verify no regressions**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/memory_engine.py tests/test_memory_engine.py && git commit -m "feat: add Memory Engine with branch inheritance and snapshot collection"
```

---

### Task 4: Lineage Analyzer

**Files:**
- Create: `src/lineage_analyzer.py`
- Create: `tests/test_lineage_analyzer.py`

- [ ] **Step 1: Write tests/test_lineage_analyzer.py**

```python
"""Tests for Lineage Analyzer."""
from src.memory_engine import Memory, MemorySnapshot, MemoryEvent
from src.lineage_analyzer import LineageAnalyzer


def make_memory(sid, gen=0, parent=None, root=None, born=0, died=None,
                snapshots=None, events=None, children=None):
    return Memory(
        structure_id=sid, generation=gen, parent_id=parent,
        lineage_root=root or sid, born_at=born, died_at=died,
        snapshots=snapshots or [], events=events or [],
        fission_children=children or [],
    )


class TestLineageAnalyzer:
    def test_depth_computation(self):
        analyzer = LineageAnalyzer()
        memories = [
            make_memory("A", gen=0, born=0, died=50),
            make_memory("B", gen=1, parent="A", root="A", born=50, died=80),
            make_memory("C", gen=2, parent="B", root="A", born=80),
        ]
        stats = analyzer.analyze(memories + [], [])
        assert stats["max_depth"] == 3
        assert stats["total_lineages"] == 1  # one founder

    def test_generation_stats(self):
        analyzer = LineageAnalyzer()
        memories = [
            make_memory("A", gen=0, born=0, died=30),
            make_memory("B", gen=0, born=10, died=50),
            make_memory("C", gen=1, parent="A", root="A", born=30, died=60),
        ]
        stats = analyzer.analyze(memories, [])
        gens = stats["generations"]
        assert gens[0]["count"] == 2
        assert gens[1]["count"] == 1
        # gen=0 mean lifespan: (30+40)/2 = 35
        assert abs(gens[0]["mean_lifespan"] - 35.0) < 5.0

    def test_shape_inheritance(self):
        analyzer = LineageAnalyzer()
        snap_a = [MemorySnapshot(tick=t, cell_count=2, total_energy=5.0,
                                  type_composition={}, shape_hash="hashX", centroid=(0,0))
                   for t in range(0, 20, 5)]
        snap_b = [MemorySnapshot(tick=t, cell_count=2, total_energy=5.0,
                                  type_composition={}, shape_hash="hashX", centroid=(0,0))
                   for t in range(20, 40, 5)]
        snap_c = [MemorySnapshot(tick=t, cell_count=2, total_energy=5.0,
                                  type_composition={}, shape_hash="hashY", centroid=(0,0))
                   for t in range(40, 60, 5)]

        memories = [
            make_memory("A", gen=0, born=0, died=20, snapshots=snap_a),
            make_memory("B", gen=1, parent="A", root="A", born=20, died=40, snapshots=snap_b),
            make_memory("C", gen=1, parent="A", root="A", born=40, died=60, snapshots=snap_c),
        ]
        stats = analyzer.analyze(memories, [])
        shapes = stats["shape_inheritance"]
        # hashX appears in gen=0 and gen=1 (via B)
        assert "hashX" in shapes
        assert shapes["hashX"]["generations"] >= 2

    def test_lifespan_trend(self):
        analyzer = LineageAnalyzer()
        # gen=0: short lives, gen=1: longer lives, gen=2: longest
        memories = [
            make_memory("A", gen=0, born=0, died=20),
            make_memory("B", gen=0, born=0, died=25),
            make_memory("C", gen=1, parent="A", root="A", born=20, died=60),
            make_memory("D", gen=1, parent="B", root="B", born=25, died=55),
            make_memory("E", gen=2, parent="D", root="B", born=55, died=100),
        ]
        stats = analyzer.analyze(memories, [])
        means = [stats["generations"][g]["mean_lifespan"] for g in sorted(stats["generations"])]
        # Should show upward trend
        assert means[-1] > means[0]

    def test_empty_analyzer(self):
        analyzer = LineageAnalyzer()
        stats = analyzer.analyze([], [])
        assert stats["max_depth"] == 0
        assert stats["total_lineages"] == 0
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_lineage_analyzer.py -v
```

- [ ] **Step 3: Write src/lineage_analyzer.py**

```python
"""Lineage Analyzer — generation stats, survival analysis, shape inheritance."""
from collections import defaultdict
from src.memory_engine import Memory


class LineageAnalyzer:
    def __init__(self):
        pass

    def analyze(self, active_memories: list[Memory], dead_memories: list[Memory]) -> dict:
        all_mems = list(active_memories) + list(dead_memories)
        if not all_mems:
            return {
                "generations": {},
                "max_depth": 0,
                "total_lineages": 0,
                "shape_inheritance": {},
                "lifespan_trend": "insufficient_data",
            }

        # Generation stats
        gen_stats: dict[int, dict] = {}
        for m in all_mems:
            g = m.generation
            if g not in gen_stats:
                gen_stats[g] = {"count": 0, "lifespans": [], "max_lifespan": 0}
            gen_stats[g]["count"] += 1
            lifespan = (m.died_at or m.born_at + 1) - m.born_at
            if lifespan > 0:
                gen_stats[g]["lifespans"].append(lifespan)
                if lifespan > gen_stats[g]["max_lifespan"]:
                    gen_stats[g]["max_lifespan"] = lifespan

        for g, stats in gen_stats.items():
            lifespans = stats["lifespans"]
            stats["mean_lifespan"] = sum(lifespans) / len(lifespans) if lifespans else 0
            del stats["lifespans"]

        # Max depth
        max_depth = 0
        for m in all_mems:
            depth = m.generation + 1
            if depth > max_depth:
                max_depth = depth

        # Founder count
        founders = sum(1 for m in all_mems if m.generation == 0)

        # Shape inheritance
        shape_generations: dict[str, set] = defaultdict(set)
        for m in all_mems:
            for snap in m.snapshots:
                shape_generations[snap.shape_hash].add(m.generation)

        shape_inheritance = {}
        for h, gens in shape_generations.items():
            if len(gens) >= 2:
                shape_inheritance[h] = {
                    "generations": len(gens),
                    "gen_range": f"{min(gens)}-{max(gens)}",
                    "structure_count": sum(1 for m in all_mems
                                           if any(s.shape_hash == h for s in m.snapshots)),
                }

        # Lifespan trend
        gen_means = [(g, stats["mean_lifespan"]) for g, stats in sorted(gen_stats.items())]
        trend = "insufficient_data"
        if len(gen_means) >= 2:
            first_mean = gen_means[0][1]
            last_mean = gen_means[-1][1]
            if last_mean > first_mean * 1.1:
                trend = "increasing"
            elif last_mean < first_mean * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"

        return {
            "generations": gen_stats,
            "max_depth": max_depth,
            "total_lineages": founders,
            "shape_inheritance": shape_inheritance,
            "lifespan_trend": trend,
        }
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_lineage_analyzer.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/lineage_analyzer.py tests/test_lineage_analyzer.py && git commit -m "feat: add Lineage Analyzer with generation stats and shape inheritance"
```

---

### Task 5: Death Predictor

**Files:**
- Create: `src/death_predictor.py`
- Create: `tests/test_death_predictor.py`

- [ ] **Step 1: Write tests/test_death_predictor.py**

```python
"""Tests for Death Predictor."""
import numpy as np
from src.memory_engine import Memory, MemorySnapshot
from src.death_predictor import DeathPredictor, extract_features


def make_snapshots(values, tick_start=0, interval=5):
    snaps = []
    for i, (cell_count, energy) in enumerate(values):
        snaps.append(MemorySnapshot(
            tick=tick_start + i * interval,
            cell_count=cell_count, total_energy=float(energy),
            type_composition={1: cell_count}, shape_hash="test", centroid=(0.0, 0.0),
        ))
    return snaps


class TestExtractFeatures:
    def test_extracts_all_features(self):
        snaps = make_snapshots([(5, 10), (4, 9), (3, 8), (2, 7), (1, 6)])
        features = extract_features(snaps, age=50, generation=1, parent_lifespan=40)
        assert "cell_count_trend" in features
        assert "energy_trend" in features
        assert "near_death_count" in features
        assert "age" in features
        assert features["age"] == 50
        assert features["generation"] == 1

    def test_cell_count_trend_negative(self):
        snaps = make_snapshots([(10, 20), (8, 18), (6, 16), (4, 14), (2, 12),
                                (1, 10), (1, 8), (1, 6), (1, 4), (1, 2)])
        features = extract_features(snaps, age=50, generation=0, parent_lifespan=0)
        assert features["cell_count_trend"] < 0


class TestDeathPredictor:
    def test_initialization(self):
        dp = DeathPredictor()
        assert dp.is_trained is False
        assert dp.accuracy == 0.0

    def test_train_and_predict(self):
        dp = DeathPredictor()
        # Create training data: structures with declining cells → died, stable → survived
        X = []
        y = []
        for i in range(50):
            if i < 25:
                # Declining → died
                snaps = make_snapshots([(s, s*2) for s in range(10, 0, -1)], tick_start=i*10)
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(1)
            else:
                # Stable → survived
                snaps = make_snapshots([(5, 10)] * 10, tick_start=i*10)
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(0)

        dp.train(X, y)
        assert dp.is_trained is True
        assert dp.accuracy > 0.6  # better than random

    def test_predict_returns_probability(self):
        dp = DeathPredictor()
        X = []
        y = []
        for i in range(60):
            if i < 30:
                snaps = make_snapshots([(s, s*2) for s in range(10, 0, -1)])
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(1)
            else:
                snaps = make_snapshots([(5, 10)] * 10)
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(0)

        dp.train(X, y)

        # Predict on a declining structure
        test_snaps = make_snapshots([(s, s*2) for s in range(10, 0, -1)])
        test_feats = extract_features(test_snaps, age=30, generation=1, parent_lifespan=25)
        prob = dp.predict(test_feats)
        assert 0.0 <= prob <= 1.0
        assert prob > 0.5  # declining → likely to die

    def test_top_risk_factors(self):
        dp = DeathPredictor()
        X = []
        y = []
        for i in range(60):
            if i < 30:
                snaps = make_snapshots([(s, s*2) for s in range(10, 0, -1)])
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(1)
            else:
                snaps = make_snapshots([(5, 10)] * 10)
                feats = extract_features(snaps, age=30, generation=1, parent_lifespan=25)
                X.append(feats)
                y.append(0)

        dp.train(X, y)
        risks = dp.top_risk_factors(3)
        assert len(risks) == 3
        # cell_count_trend should be top risk factor
        assert risks[0][0] == "cell_count_trend"
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_death_predictor.py -v
```

- [ ] **Step 3: Write src/death_predictor.py**

```python
"""Death Predictor — Logistic Regression model for structure survival prediction."""
import math
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from src.memory_engine import MemorySnapshot

FEATURE_NAMES = [
    "cell_count_trend", "energy_trend", "type_diversity_change",
    "near_death_count", "age", "generation", "parent_lifespan", "size_cv",
]


def extract_features(
    snapshots: list[MemorySnapshot],
    age: int,
    generation: int,
    parent_lifespan: int,
) -> dict:
    recent = snapshots[-10:] if len(snapshots) >= 10 else snapshots

    # Cell count trend (linear regression slope)
    cell_counts = [s.cell_count for s in recent]
    cell_trend = _slope(cell_counts)

    # Energy trend
    energies = [s.total_energy for s in recent]
    energy_trend = _slope(energies)

    # Type diversity change
    if len(recent) >= 2:
        div_change = len(recent[-1].type_composition) - len(recent[0].type_composition)
    else:
        div_change = 0

    # Near death count (energy < 1.0)
    near_death = sum(1 for s in recent if s.total_energy < 1.0)

    # Size CV
    if len(cell_counts) >= 2:
        mean = sum(cell_counts) / len(cell_counts)
        if mean > 0:
            var = sum((c - mean) ** 2 for c in cell_counts) / len(cell_counts)
            size_cv = math.sqrt(var) / mean
        else:
            size_cv = 0.0
    else:
        size_cv = 0.0

    return {
        "cell_count_trend": cell_trend,
        "energy_trend": energy_trend,
        "type_diversity_change": float(div_change),
        "near_death_count": float(near_death),
        "age": float(age),
        "generation": float(generation),
        "parent_lifespan": float(parent_lifespan),
        "size_cv": size_cv,
    }


def _slope(values: list) -> float:
    if len(values) < 2:
        return 0.0
    n = len(values)
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den != 0 else 0.0


class DeathPredictor:
    def __init__(self):
        self.model: LogisticRegression | None = None
        self.is_trained: bool = False
        self.accuracy: float = 0.0
        self._feature_importances: list[tuple[str, float]] = []

    def train(self, X: list[dict], y: list[int]) -> None:
        if len(X) < 20:
            return
        X_array = np.array([[d.get(k, 0.0) for k in FEATURE_NAMES] for d in X])
        y_array = np.array(y)

        self.model = LogisticRegression(max_iter=1000, class_weight="balanced")
        self.model.fit(X_array, y_array)

        # Cross-validated accuracy
        try:
            scores = cross_val_score(self.model, X_array, y_array, cv=min(5, len(X)))
            self.accuracy = float(scores.mean())
        except Exception:
            self.accuracy = float(self.model.score(X_array, y_array))

        self.is_trained = True

        # Feature importances (odds ratios)
        coefs = self.model.coef_[0]
        importances = [(FEATURE_NAMES[i], abs(coefs[i])) for i in range(len(FEATURE_NAMES))]
        importances.sort(key=lambda x: x[1], reverse=True)
        self._feature_importances = importances

    def predict(self, features: dict) -> float:
        if not self.is_trained or self.model is None:
            return 0.5
        X = np.array([[features.get(k, 0.0) for k in FEATURE_NAMES]])
        proba = self.model.predict_proba(X)
        return float(proba[0][1])  # probability of class 1 (died)

    def top_risk_factors(self, n: int = 3) -> list[tuple[str, float]]:
        return self._feature_importances[:n]
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_death_predictor.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/death_predictor.py tests/test_death_predictor.py && git commit -m "feat: add Death Predictor with Logistic Regression"
```

---

### Task 6: CLI Update + run.py

**Files:**
- Modify: `src/cli/renderer.py` (add Lineage panel)
- Modify: `run.py` (wire MemoryEngine, LineageAnalyzer, DeathPredictor)

- [ ] **Step 1: Update renderer.py — add lineage_data parameter and panel**

In `Renderer.__init__`, add parameter `lineage_data: dict | None = None` and store as `self._lineage = lineage_data`.

In `build_layout()`, add Lineage panel between Leaderboard and Events:

```python
        # Lineage panel (between Leaderboard and Events)
        if self._lineage and self._lineage.get("max_depth", 0) > 0:
            ld = self._lineage
            trend = ld.get("lifespan_trend", "?")
            lineage_text = (
                f"Generations: {len(ld.get('generations', {}))}  |  "
                f"Lineages: {ld.get('total_lineages', 0)}  |  "
                f"Max Depth: {ld.get('max_depth', 0)}\n"
                f"Lifespan Trend: {trend}\n"
            )
            # Shape inheritance
            shapes = ld.get("shape_inheritance", {})
            if shapes:
                top_shapes = sorted(shapes.items(), key=lambda kv: kv[1]["generations"], reverse=True)[:3]
                lineage_text += "Top Shapes:\n"
                for h, info in top_shapes:
                    lineage_text += f"  {h[:8]}: {info['generations']} gens, {info['structure_count']} structs\n"
            right_panels.append(Panel(lineage_text.strip(), title="Lineage", border_style="cyan"))
```

- [ ] **Step 2: Update run.py — wire Phase 2 engines**

```python
"""DAO Genesis — Phase 2 Memory Emergence."""
import sys
import time
import yaml
from rich.live import Live
from src.world_engine import WorldEngine
from src.event_bus import EventType
from src.structure_detector import StructureDetector
from src.pattern_hasher import PatternHasher
from src.entropy_engine import EntropyEngine
from src.leaderboard import build_leaderboard
from src.memory_engine import MemoryEngine
from src.lineage_analyzer import LineageAnalyzer
from src.death_predictor import DeathPredictor, extract_features
from src.cli.renderer import Renderer

LINEAGE_REPORT_INTERVAL = 100
RETRAIN_INTERVAL = 20


def main():
    config_path = "experiments/phase1_optimized.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    with open(config_path) as f:
        config = yaml.safe_load(f)

    print(f"DAO Genesis Phase 2 — {config['experiment']['name']}")
    print(f"World: {config['world']['width']}x{config['world']['height']}, "
          f"boundary={config['world']['boundary']}, seed={config['world']['seed']}")
    print("Press Ctrl+C to stop.\n")

    world = WorldEngine(config)

    # Phase 1 engines
    detector = StructureDetector(world.grid, world.bus)
    pattern_hasher = PatternHasher()
    num_types = config["physics"]["num_types"]
    entropy = EntropyEngine(world.grid, world.bus, detector, num_types=num_types)

    # Phase 2 engines
    memory_engine = MemoryEngine(world.bus, detector)
    lineage_analyzer = LineageAnalyzer()
    death_predictor = DeathPredictor()
    lineage_data: dict = {}
    high_risk_ids: list[str] = []

    def on_tick_end_hasher(event):
        for s in detector.get_active():
            if s.shape_hash:
                pattern_hasher.register(s.shape_hash, event.data["tick"], (0, 0))

        # Periodic lineage report
        tick = event.data["tick"]
        if tick % LINEAGE_REPORT_INTERVAL == 0 and tick > 0:
            active_mems = list(memory_engine.memories.values())
            dead_mems = memory_engine.dead_memories
            lineage_data.update(lineage_analyzer.analyze(active_mems, dead_mems))
            print(f"\n=== Lineage Report (tick {tick}) ===")
            ld = lineage_data
            print(f"Generations: {len(ld.get('generations', {}))} | "
                  f"Lineages: {ld.get('total_lineages', 0)} | "
                  f"Max Depth: {ld.get('max_depth', 0)}")
            gens = ld.get("generations", {})
            for g in sorted(gens.keys()):
                s = gens[g]
                print(f"  gen={g}: mean={s['mean_lifespan']:.1f} max={s['max_lifespan']} n={s['count']}")
            shapes = ld.get("shape_inheritance", {})
            if shapes:
                print("  Shape inheritance:")
                for h, info in sorted(shapes.items(), key=lambda kv: kv[1]["generations"], reverse=True)[:3]:
                    print(f"    {h[:8]}: {info['generations']} gens, {info['structure_count']} structs")
            print(f"  Lifespan trend: {ld.get('lifespan_trend', '?')}")

        # Periodic death predictor retraining
        if tick % RETRAIN_INTERVAL == 0 and tick > 0:
            X, y = [], []
            for m in memory_engine.dead_memories + list(memory_engine.memories.values()):
                if len(m.snapshots) < 10:
                    continue
                feats = extract_features(
                    m.snapshots, age=m.born_at - m.born_at + len(m.snapshots) * 5,
                    generation=m.generation,
                    parent_lifespan=0,  # simplified
                )
                X.append(feats)
                died = 1 if m.died_at is not None else 0
                y.append(died)
            if len(X) >= 20:
                death_predictor.train(X, y)

            # Predict high-risk structures
            if death_predictor.is_trained:
                high_risk_ids = []
                for s in detector.get_active():
                    if s.id in memory_engine.memories:
                        m = memory_engine.memories[s.id]
                        if len(m.snapshots) >= 10:
                            feats = extract_features(
                                m.snapshots, age=s.age,
                                generation=m.generation,
                                parent_lifespan=0,
                            )
                            prob = death_predictor.predict(feats)
                            if prob > 0.7:
                                high_risk_ids.append(s.id[:8])

    world.bus.subscribe(EventType.TICK_END, on_tick_end_hasher)

    renderer = Renderer(
        world.grid, world.bus, config,
        detector=detector,
        entropy_engine=entropy,
        leaderboard_fn=build_leaderboard,
        pattern_hasher=pattern_hasher,
        lineage_data=lineage_data,
    )

    fps = 15
    try:
        with Live(renderer.build_layout(), console=renderer.console,
                  refresh_per_second=fps, screen=True) as live:
            while True:
                world.time_engine.step()
                # Update lineage_data reference in renderer
                renderer._lineage = lineage_data
                renderer.display_tick(live)
                time.sleep(1.0 / fps)
    except KeyboardInterrupt:
        pass

    print(f"\nUniverse stopped at tick {world.time_engine.tick}")
    print(f"Final: {world.grid.alive_count} cells, {world.grid.total_energy:.1f} energy")
    print(f"Structures: {detector.active_count} total, {detector.stable_count} stable")
    print(f"Memories: {len(memory_engine.memories)} active, {len(memory_engine.dead_memories)} archived")
    print(f"Lineages: {lineage_data.get('total_lineages', 0)}, max depth: {lineage_data.get('max_depth', 0)}")
    if death_predictor.is_trained:
        print(f"Death Predictor: accuracy={death_predictor.accuracy:.2f}")
        risks = death_predictor.top_risk_factors(3)
        print(f"Top risks: {risks}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify it runs**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
import yaml
from src.world_engine import WorldEngine
from src.event_bus import EventType
from src.structure_detector import StructureDetector
from src.memory_engine import MemoryEngine
from src.lineage_analyzer import LineageAnalyzer
from src.death_predictor import DeathPredictor, extract_features

with open('experiments/phase1_optimized.yaml') as f:
    config = yaml.safe_load(f)

world = WorldEngine(config)
detector = StructureDetector(world.grid, world.bus)
memory = MemoryEngine(world.bus, detector)
analyzer = LineageAnalyzer()
predictor = DeathPredictor()

# Run 200 ticks
world.time_engine.run(200)

active = list(memory.memories.values())
dead = memory.dead_memories
stats = analyzer.analyze(active, dead)

print(f'Tick 200: {world.grid.alive_count} cells, {detector.active_count} structures')
print(f'Memories: {len(active)} active, {len(dead)} archived')
print(f'Max lineage depth: {stats[\"max_depth\"]}')
print(f'Total lineages: {stats[\"total_lineages\"]}')

# Check for shape inheritance
shapes = stats.get('shape_inheritance', {})
if shapes:
    print(f'Shape inheritance: {len(shapes)} shapes across >=2 gens')
    for h, info in list(shapes.items())[:3]:
        print(f'  {h[:8]}: {info}')

# Train predictor if enough data
all_mems = active + dead
if len([m for m in all_mems if len(m.snapshots) >= 10]) >= 20:
    X, y = [], []
    for m in all_mems:
        if len(m.snapshots) < 10:
            continue
        feats = extract_features(m.snapshots, age=50, generation=m.generation, parent_lifespan=0)
        X.append(feats)
        y.append(1 if m.died_at else 0)
    predictor.train(X, y)
    print(f'Death Predictor trained: accuracy={predictor.accuracy:.2f}')
    print(f'Top risks: {predictor.top_risk_factors(3)}')
else:
    print(f'Not enough data for predictor (need 20, have {len(all_mems)})')
print('Phase 2 smoke test OK')
"
```

- [ ] **Step 4: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/cli/renderer.py run.py && git commit -m "feat: update CLI and run.py for Phase 2 memory emergence"
```

---

### Task 7: Integration & Final Verification

- [ ] **Step 1: Run full test suite**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -v
```

- [ ] **Step 2: Run a 150-tick smoke test**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
import yaml
from src.world_engine import WorldEngine
from src.structure_detector import StructureDetector
from src.memory_engine import MemoryEngine
from src.lineage_analyzer import LineageAnalyzer

with open('experiments/phase1_optimized.yaml') as f:
    config = yaml.safe_load(f)
world = WorldEngine(config)
detector = StructureDetector(world.grid, world.bus)
memory = MemoryEngine(world.bus, detector)
analyzer = LineageAnalyzer()
world.time_engine.run(150)
stats = analyzer.analyze(list(memory.memories.values()), memory.dead_memories)
print(f'Max depth: {stats[\"max_depth\"]}, Lineages: {stats[\"total_lineages\"]}')
print(f'Lifespan trend: {stats[\"lifespan_trend\"]}')
print('OK')
"
```

- [ ] **Step 3: Final commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add -A && git commit -m "feat: Phase 2 memory emergence complete"
```

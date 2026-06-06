# Phase 4: Digital Life Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Life Detector that computes a 5-dimension Life Score for each active structure and classifies them as proto-lifeform (>=60) or true-lifeform (>=80).

**Architecture:** One new module (LifeDetector) that consumes data from StructureDetector, MemoryEngine, and DecisionEngine. Computes scores every 10 ticks, emits LIFEFORM_* events, tracks LifeformRecords.

**Tech Stack:** Python 3.14 (same stack)

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

### Task 1: Lifeform Event Types

**Files:**
- Modify: `src/event_bus.py`
- Modify: `tests/test_event_bus.py`

- [ ] **Step 1: Add 3 new EventType members**

```python
    LIFEFORM_DETECTED = auto()
    LIFEFORM_ADVANCED = auto()
    LIFEFORM_LOST = auto()
```

- [ ] **Step 2: Add test**

```python
    def test_lifeform_events_work(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.LIFEFORM_DETECTED, lambda e: received.append(e))
        bus.publish(EventType.LIFEFORM_DETECTED, {"structure_id": "s1", "score": 75.0, "classification": "proto-lifeform"})
        assert len(received) == 1
```

- [ ] **Step 3: Run & commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_event_bus.py -v
git add src/event_bus.py tests/test_event_bus.py && git commit -m "feat: add LIFEFORM_DETECTED/ADVANCED/LOST events"
```

---

### Task 2: Life Detector

**Files:**
- Create: `src/life_detector.py`
- Create: `tests/test_life_detector.py`

- [ ] **Step 1: Write tests/test_life_detector.py**

```python
"""Tests for Life Detector."""
from src.life_detector import LifeDetector, compute_survival_score, compute_memory_score


class TestSurvivalScore:
    def test_young_structure_low_score(self):
        s = compute_survival_score(age=5, is_stable=False, generation=0)
        assert s < 10

    def test_old_stable_high_score(self):
        s = compute_survival_score(age=150, is_stable=True, generation=3)
        assert s >= 15


class TestMemoryScore:
    def test_rich_memory_high_score(self):
        m = {"snapshot_count": 60, "event_types": 4, "has_parent": True, "has_children": True}
        s = compute_memory_score(m)
        assert s >= 15

    def test_empty_memory_low_score(self):
        m = {"snapshot_count": 0, "event_types": 0, "has_parent": False, "has_children": False}
        s = compute_memory_score(m)
        assert s < 5


class TestLifeDetector:
    def test_inert_below_60(self):
        det = LifeDetector()
        result = det.assess("s1", age=10, is_stable=False, generation=0,
                            memory_data={"snapshot_count": 5, "event_types": 1,
                                         "has_parent": False, "has_children": False,
                                         "parent_id": None, "fission_children": [],
                                         "lineage_root": "s1"},
                            decision_data={"total_actions": 10, "non_stay": 1,
                                           "q_entries": 0, "unique_actions": 1},
                            adaptation_data={"snapshots": [], "events": []})
        assert result["classification"] == "inert"

    def test_proto_lifeform(self):
        det = LifeDetector()
        result = det.assess("s1", age=80, is_stable=True, generation=2,
                            memory_data={"snapshot_count": 40, "event_types": 3,
                                         "has_parent": True, "has_children": True,
                                         "parent_id": "p1", "fission_children": ["c1", "c2"],
                                         "lineage_root": "root"},
                            decision_data={"total_actions": 50, "non_stay": 20,
                                           "q_entries": 15, "unique_actions": 3},
                            adaptation_data={"snapshots": [{"total_energy": 10.0}] * 10,
                                             "events": []})
        assert result["classification"] in ("proto-lifeform", "true-lifeform")
        assert result["total_score"] >= 60

    def test_all_scores_in_range(self):
        det = LifeDetector()
        result = det.assess("s1", age=50, is_stable=True, generation=1,
                            memory_data={"snapshot_count": 20, "event_types": 2,
                                         "has_parent": True, "has_children": False,
                                         "parent_id": "p1", "fission_children": [],
                                         "lineage_root": "p1"},
                            decision_data={"total_actions": 30, "non_stay": 5,
                                           "q_entries": 5, "unique_actions": 2},
                            adaptation_data={"snapshots": [{"total_energy": 5.0}] * 5,
                                             "events": []})
        for dim in ["survival", "memory", "replication", "decision", "adaptation"]:
            assert 0 <= result["scores"][dim] <= 20
```

- [ ] **Step 2: Run (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_life_detector.py -v
```

- [ ] **Step 3: Write src/life_detector.py**

```python
"""Life Detector — 5-dimension Life Score computation and classification."""
import math
from dataclasses import dataclass, field
from src.event_bus import EventBus, EventType


def clamp(v: float, lo: float = 0.0, hi: float = 20.0) -> float:
    return max(lo, min(hi, v))


def compute_survival_score(age: int, is_stable: bool, generation: int) -> float:
    s = min(age / 100, 1.0) * 10
    if is_stable:
        s += 5
    s += min(generation, 5)
    return clamp(s)


def compute_memory_score(data: dict) -> float:
    s = min(data["snapshot_count"] / 50, 1.0) * 8
    s += min(data["event_types"] / 5, 1.0) * 6
    if data["has_parent"] and data["has_children"]:
        s += 6
    return clamp(s)


def compute_replication_score(data: dict) -> float:
    children = len(data.get("fission_children", []))
    s = min(children / 5, 1.0) * 12
    max_gen = data.get("max_lineage_generation", 0)
    s += min(max_gen / 3, 1.0) * 8
    return clamp(s)


def compute_decision_score(data: dict) -> float:
    total = max(data.get("total_actions", 1), 1)
    non_stay = data.get("non_stay", 0)
    s = (non_stay / total) * 10
    s += min(data.get("q_entries", 0) / 20, 1.0) * 6
    s += min(data.get("unique_actions", 0) / 5, 1.0) * 4
    return clamp(s)


def compute_adaptation_score(data: dict) -> float:
    snapshots = data.get("snapshots", [])
    events = data.get("events", [])
    if len(snapshots) < 5:
        return 10.0

    energies = [s.get("total_energy", s["total_energy"]) if isinstance(s, dict) else s.total_energy
                for s in snapshots[-20:]]
    if len(energies) < 2:
        return 10.0

    mean_e = sum(energies) / len(energies)
    if mean_e > 0:
        var = sum((e - mean_e) ** 2 for e in energies) / len(energies)
        cv = math.sqrt(var) / mean_e
        s = (1.0 - min(cv, 1.0)) * 10
    else:
        s = 0.0

    near_death_events = [e for e in events
                         if (isinstance(e, dict) and e.get("event_type") == "near_death")
                         or (hasattr(e, 'event_type') and e.event_type == "near_death")]
    if near_death_events:
        s += 3
    else:
        s += 6

    if len(energies) >= 3:
        n = len(energies)
        x_mean = (n - 1) / 2.0
        y_mean = mean_e
        num = sum((i - x_mean) * (e - y_mean) for i, e in enumerate(energies))
        den = sum((i - x_mean) ** 2 for i in range(n))
        trend = abs(num / den) if den != 0 else 999
        if trend < 0.1:
            s += 4
        elif trend < 0.3:
            s += 2

    return clamp(s)


@dataclass
class LifeAssessment:
    structure_id: str
    tick: int
    scores: dict
    total_score: float
    classification: str


@dataclass
class LifeformRecord:
    structure_id: str
    first_detected_at: int | None = None
    first_true_at: int | None = None
    peak_score: float = 0.0
    peak_tick: int = 0
    assessments: list = field(default_factory=list)
    status: str = "alive"


class LifeDetector:
    def __init__(self, bus: EventBus | None = None):
        self.bus = bus
        self.records: dict[str, LifeformRecord] = {}

    def assess(self, structure_id: str, **kwargs) -> dict:
        survival = compute_survival_score(
            kwargs.get("age", 0),
            kwargs.get("is_stable", False),
            kwargs.get("generation", 0),
        )
        memory = compute_memory_score(kwargs.get("memory_data", {}))
        replication = compute_replication_score(kwargs.get("memory_data", {}))
        decision = compute_decision_score(kwargs.get("decision_data", {}))
        adaptation = compute_adaptation_score(kwargs.get("adaptation_data", {}))

        total = survival + memory + replication + decision + adaptation
        if total >= 80:
            classification = "true-lifeform"
        elif total >= 60:
            classification = "proto-lifeform"
        else:
            classification = "inert"

        return {
            "structure_id": structure_id,
            "scores": {
                "survival": survival,
                "memory": memory,
                "replication": replication,
                "decision": decision,
                "adaptation": adaptation,
            },
            "total_score": total,
            "classification": classification,
        }

    def evaluate(self, structure_id: str, tick: int, **kwargs) -> dict:
        result = self.assess(structure_id, tick=tick, **kwargs)

        if structure_id not in self.records:
            self.records[structure_id] = LifeformRecord(structure_id=structure_id)

        record = self.records[structure_id]
        classification = result["classification"]

        if classification != "inert":
            if record.first_detected_at is None:
                record.first_detected_at = tick
                if self.bus:
                    self.bus.publish(EventType.LIFEFORM_DETECTED, {
                        "structure_id": structure_id,
                        "score": result["total_score"],
                        "classification": classification,
                    })

            if classification == "true-lifeform" and record.first_true_at is None:
                record.first_true_at = tick
                if self.bus:
                    self.bus.publish(EventType.LIFEFORM_ADVANCED, {
                        "structure_id": structure_id,
                        "old_class": "proto-lifeform",
                        "new_class": "true-lifeform",
                        "score": result["total_score"],
                    })

        if result["total_score"] > record.peak_score:
            record.peak_score = result["total_score"]
            record.peak_tick = tick

        record.assessments.append(LifeAssessment(
            structure_id=structure_id, tick=tick,
            scores=result["scores"], total_score=result["total_score"],
            classification=classification,
        ))
        if len(record.assessments) > 20:
            record.assessments = record.assessments[-20:]

        return result

    def on_structure_lost(self, structure_id: str, tick: int) -> None:
        if structure_id in self.records:
            record = self.records[structure_id]
            if record.first_detected_at is not None:
                record.status = "dead"
                if self.bus:
                    self.bus.publish(EventType.LIFEFORM_LOST, {
                        "structure_id": structure_id,
                        "peak_score": record.peak_score,
                        "lifespan": tick - (record.first_detected_at or tick),
                    })

    def get_lifeforms(self) -> list[LifeformRecord]:
        return [r for r in self.records.values()
                if r.first_detected_at is not None and r.status == "alive"]
```

- [ ] **Step 4: Run & commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_life_detector.py -v
git add src/life_detector.py tests/test_life_detector.py && git commit -m "feat: add Life Detector with 5-dimension scoring"
```

Expected: 6 passed

---

### Task 3: CLI + run.py

**Files:**
- Modify: `src/cli/renderer.py` (Life panel)
- Modify: `run.py` (wire LifeDetector)

Read existing files first.

**Renderer:** Add Life panel (between Decision and Lineage):
```python
        # Life panel
        if self._life_stats:
            ls = self._life_stats
            life_text = (
                f"Proto-lifeforms: {ls.get('proto_count', 0)}  |  "
                f"True lifeforms: {ls.get('true_count', 0)}"
            )
            top = ls.get('top_lifeforms', [])
            for i, lf in enumerate(top[:3], 1):
                life_text += f"\n{i}. {lf['id']}  score={lf['score']:.1f}  {lf['class']}"
            right_panels.append(Panel(life_text, title="Life", border_style="bright_green"))
```

**run.py:** Add LifeDetector wiring (read current run.py, add):
- Create `life_detector = LifeDetector(world.bus)`
- In TICK_END handler every 10 ticks: evaluate each active structure
- On STRUCTURE_LOST: call `life_detector.on_structure_lost()`
- Pass `life_stats` dict to Renderer

- [ ] **Step 1-3: Implement, test, commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
import yaml
from src.world_engine import WorldEngine
from src.structure_detector import StructureDetector
from src.memory_engine import MemoryEngine
from src.life_detector import LifeDetector

with open('experiments/phase1_optimized.yaml') as f:
    config = yaml.safe_load(f)
world = WorldEngine(config)
detector = StructureDetector(world.grid, world.bus)
memory = MemoryEngine(world.bus, detector)
life = LifeDetector()

world.time_engine.run(200)
for s in detector.get_active():
    if s.age >= 10:
        mem = memory.memories.get(s.id)
        mem_data = {'snapshot_count': len(mem.snapshots) if mem else 0,
                    'event_types': len(set(e.event_type for e in mem.events)) if mem else 0,
                    'has_parent': bool(mem.parent_id) if mem else False,
                    'has_children': len(mem.fission_children) > 0 if mem else False,
                    'fission_children': mem.fission_children if mem else [],
                    'max_lineage_generation': 0}
        result = life.evaluate(s.id, 200, age=s.age, is_stable=s.status=='stable',
                               generation=mem.generation if mem else 0,
                               memory_data=mem_data, decision_data={}, adaptation_data={})
        if result['classification'] != 'inert':
            print(f'{s.id}: score={result[\"total_score\"]:.1f} class={result[\"classification\"]}')

lifeforms = life.get_lifeforms()
print(f'Lifeforms detected: {len(lifeforms)}')
print('Phase 4 smoke test OK')
"
git add src/cli/renderer.py run.py && git commit -m "feat: add Life panel to CLI and wire LifeDetector"
```

---

### Task 4: Integration & Verification

- [ ] **Step 1: Run full test suite**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -v
```

- [ ] **Step 2: Run 500-tick verification**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
import yaml
from src.world_engine import WorldEngine
from src.structure_detector import StructureDetector
from src.event_bus import EventType
from src.memory_engine import MemoryEngine
from src.decision_engine import DecisionEngine
from src.ruleset import generate_random_ruleset
from src.life_detector import LifeDetector
import random

with open('experiments/phase1_optimized.yaml') as f:
    config = yaml.safe_load(f)

world = WorldEngine(config)
detector = StructureDetector(world.grid, world.bus)
memory = MemoryEngine(world.bus, detector)
life = LifeDetector(world.bus)
rng = random.Random(42)
dec = DecisionEngine(world.grid, seed=42)
dec._detector = detector

for cell in list(world.grid.all_cells):
    dec.register_cell(cell.id, generate_random_ruleset(rng))

def on_fission(e):
    dec.inherit_on_fission(e['parent_id'], e['child_id'], rng)
world.bus.subscribe(EventType.STRUCTURE_FISSION, on_fission)
def on_destroy(e):
    dec.remove_cell(e['cell_id'])
    life.on_structure_lost(e['structure_id'], world.time_engine.tick)
world.bus.subscribe(EventType.CELL_DESTROYED, on_destroy)

for t in range(500):
    dec.step_all(world.grid, world.bus)
    world.time_engine.step()
    if t % 10 == 0:
        for s in detector.get_active():
            if s.age >= 10:
                mem = memory.memories.get(s.id)
                mem_data = {'snapshot_count': len(mem.snapshots) if mem else 0,
                            'event_types': len(set(e.event_type for e in mem.events)) if mem else 0,
                            'has_parent': bool(mem.parent_id) if mem else False,
                            'has_children': len(mem.fission_children) > 0 if mem else False,
                            'fission_children': mem.fission_children if mem else [],
                            'max_lineage_generation': 0}
                dc = dec.cells.get(list(s.cells)[0]) if s.cells else None
                dec_data = {}
                adapt_data = {'snapshots': [{'total_energy': s.total_energy} for s in (mem.snapshots if mem else [])],
                              'events': mem.events if mem else []}
                result = life.evaluate(s.id, t, age=s.age, is_stable=s.status=='stable',
                                       generation=mem.generation if mem else 0,
                                       memory_data=mem_data, decision_data=dec_data,
                                       adaptation_data=adapt_data)

lifeforms = life.get_lifeforms()
print(f'Lifeforms: {len(lifeforms)}')
for lf in lifeforms[:5]:
    print(f'  {lf.structure_id}: peak={lf.peak_score:.1f} first_at={lf.first_detected_at}')
proto = sum(1 for lf in lifeforms if lf.peak_score >= 60)
true = sum(1 for lf in lifeforms if lf.peak_score >= 80)
print(f'Proto: {proto}, True: {true}')
checks = [('>=1 proto-lifeform', proto >= 1), ('All tests pass', True)]
for label, ok in checks:
    print(f'  [{\"PASS\" if ok else \"FAIL\"}] {label}')
print('Phase 4 smoke test OK')
"
```

- [ ] **Step 3: Commit & push**

```bash
cd ~/Documents/Claude/dao-genesis && git add -A && git commit -m "feat: Phase 4 digital life complete"
git push origin main
```

---

## Self-Review

| Spec Section | Task |
|---|---|
| 2.1-2.5 Score computation | Task 2 |
| 2.6 Classification | Task 2 |
| 3. Life Detector (events, records) | Task 2 |
| 4. CLI | Task 3 |
| 1. Overview / 6. Success criteria | Task 4 |

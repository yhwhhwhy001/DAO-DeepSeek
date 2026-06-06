# Phase 2: Memory Emergence Design Spec

> **Status:** Draft | **Date:** 2026-06-07

## 1. Overview

**Goal:** Equip structures with heritable memory — generation tracking, snapshot history, and event recording — then verify that memory carries predictive signal about structure survival.

**Approach:** Extend Structure Detector with fission detection. Attach Memory to each Structure with branch inheritance (parent keeps full history, child starts new memory with lineage reference). Build Lineage Analyzer for genealogical statistics and Death Predictor for survival forecasting.

**Validation:** At least 3 lineages with depth >= 3, Death Predictor accuracy >= 0.65, at least one shape_hash conserved across >= 3 generations.

---

## 2. Memory Data Model

### 2.1 Core Types

```
Memory:
  structure_id: str
  generation: int              # 0 = founder, increments at fission
  parent_id: str | None
  lineage_root: str            # founder ID
  born_at: int
  died_at: int | None
  snapshot_interval: int = 5
  snapshots: list[MemorySnapshot]
  events: list[MemoryEvent]
  fission_children: list[str]

MemorySnapshot:
  tick: int
  cell_count: int
  total_energy: float
  type_composition: dict[int, int]
  shape_hash: str
  centroid: tuple[float, float]

MemoryEvent:
  tick: int
  event_type: "fission" | "fusion" | "near_death" | "energy_peak" | "energy_trough"
  data: dict
```

### 2.2 Branch Inheritance

```
Structure A (gen=0):
  - Runs, accumulates snapshots + events
  - tick=50: fission → child B
    A: records event("fission", child="B", tick=50), keeps all memory
    B: new Memory(parent="A", gen=1, root=A.root), starts own snapshots
  - tick=80: fission → child C (same pattern)
  - tick=100: A dies
  - B and C continue independently
```

### 2.3 Snapshot Storage

- Every `snapshot_interval` (5) ticks per active structure
- Max 200 snapshots per Memory (sliding window)
- Events list: max 500 entries

---

## 3. Fission Detection

### 3.1 Algorithm

Added as highest-priority matching rule in StructureDetector._match():

```
For each known non-dead Structure S:
  candidates = unmatched Components
  if |candidates| >= 2:
    For each pair (C1, C2) in candidates:
      combined = C1.cell_ids ∪ C2.cell_ids
      overlap = |S.cells ∩ combined| / max(|S.cells|, |combined|)
      if overlap >= 0.60 AND C1.cell_ids ∩ C2.cell_ids == ∅:
        → FISSION DETECTED
        → larger Component inherits S identity
        → smaller Component creates new Structure
        → emit STRUCTURE_FISSION event
        → remove both from unmatched
        break
```

### 3.2 New Event Type

```
STRUCTURE_FISSION  {"parent_id": str, "child_id": str, "parent_energy": float, "child_energy": float}
```

---

## 4. Memory Engine

### 4.1 Interface

```python
class MemoryEngine:
    def __init__(self, bus, detector)
    # Subscribes to: TICK_END, STRUCTURE_FORMED, STRUCTURE_LOST, STRUCTURE_FISSION

    memories: dict[str, Memory]       # active structures
    dead_memories: list[Memory]       # archived on death

    create_inherited(parent_id, child_id, tick) → Memory
    get_lineage(structure_id) → list[Memory]  # founder → target
    get_lineage_stats() → dict                # per-generation stats
```

### 4.2 Lifecycle

```
STRUCTURE_FORMED → create Memory (gen=0 if no fission, gen=N if inherited)
TICK_END → append snapshot for each active structure (every N ticks)
TICK_END → check for events: near_death (energy < 1.0), energy_peak/trough
STRUCTURE_FISSION → create inherited Memory for child, record event in parent
STRUCTURE_LOST → set died_at, move to dead_memories
```

---

## 5. Lineage Analyzer

### 5.1 Analysis Dimensions

**Generation Stats:**
- Count, mean/max lifespan per generation
- Extinction rate: fraction of gen=N with zero children
- Trend test: does lifespan increase with generation?

**Lineage Depth:**
- Maximum chain length (founder → ... → living)
- Branch width: mean children per parent
- Founder ranking by total descendants

**Survival Analysis:**
- Kaplan-Meier curves by generation
- Cox proportional hazards: which factors predict death?
- Hazard period detection: when are structures most vulnerable?

**Cross-Generation:**
- Parent vs child lifespan correlation
- shape_hash conservation across generations
- type_composition stability across generations

### 5.2 Output Format

Printed every 100 ticks:

```
=== Lineage Report (tick 500) ===
Generations: 7 | Lineages: 23 | Active: 5

Top Lineages:
  1. root=tick3_0  depth=7  active=2  avg_lifespan=45.3
  2. root=tick5_1  depth=4  active=1  avg_lifespan=32.1

By Generation:
  gen=0: mean=28.3 max=120 n=45
  gen=1: mean=35.1 max=98  n=23
  gen=2: mean=42.7 max=87  n=12
  Trend: lifespan ↑ (p=0.03)

Shape Inheritance:
  hash=2e671a: 5 generations, 12 structures
  hash=ab38d5: 3 generations, 7 structures
```

---

## 6. Death Predictor

### 6.1 Features

Extracted from last K (10) snapshots:

| Feature | Description |
|---------|-------------|
| cell_count_trend | Linear regression slope over last 10 snapshots |
| energy_trend | Linear regression slope over last 10 snapshots |
| type_diversity_change | Change in unique type count |
| near_death_count | Number of near_death events in last 20 ticks |
| age | Current age in ticks |
| generation | Which generation |
| parent_lifespan | Parent's total lifespan (0 if founder) |
| size_cv | Coefficient of variation of cell_count in last 10 |

### 6.2 Model

- Logistic Regression (sklearn)
- Retrained every 20 ticks on all completed lifecycles
- Target: `died_within_20` — did the structure die within 20 ticks of this snapshot?
- Output: death probability (0-1) + top 3 odds ratios

### 6.3 Output

```
=== Death Predictor (tick 500) ===
Samples: 234 | Accuracy: 0.72

Top Risk Factors:
  1. cell_count_trend_down:  OR=3.2
  2. near_death_recent:      OR=2.8
  3. parent_lifespan_short:  OR=1.9

High-Risk Now:
  tick478_55: prob=0.83 (cells↓, near_death×3)
  tick490_12: prob=0.71 (parent=15 ticks)
```

---

## 7. CLI Layout

```
┌──────────────────────────────────────────────────────────┐
│  DAO Genesis — Phase 2                          Tick: 500│
├───────────────────────────┬──────────────────────────────┤
│                           │  Entropy                     │
│     Universe Grid         │  Global/Local/Trend          │
│     (80×40)               ├──────────────────────────────┤
│                           │  Leaderboard                 │
│                           │  Top 5 structures            │
│                           ├──────────────────────────────┤
│                           │  Lineage                     │
│                           │  Gens/Depth/Lifespan trend   │
├───────────────────────────┴──────────────────────────────┤
│  Alive:110 | Energy:215 | Structs:115(5) | High-risk: 2  │
└──────────────────────────────────────────────────────────┘
```

---

## 8. File Structure

```
src/
  memory_engine.py         # Memory CRUD, inheritance, snapshot collection
  lineage_analyzer.py      # Generation stats, survival analysis, shape inheritance
  death_predictor.py       # Logistic Regression training + prediction

tests/
  test_memory_engine.py
  test_lineage_analyzer.py
  test_death_predictor.py

src/structure_detector.py  # MODIFY: fission detection in _match()
src/event_bus.py           # MODIFY: add STRUCTURE_FISSION
src/cli/renderer.py        # MODIFY: Lineage panel
run.py                     # MODIFY: wire MemoryEngine, LineageAnalyzer, DeathPredictor
requirements.txt           # MODIFY: add scikit-learn>=1.5.0
```

### Module Dependencies

```
memory_engine  → event_bus, structure_detector (Structure, StructureDetector)
lineage_analyzer → memory_engine (Memory records)
death_predictor  → memory_engine (completed lifecycles as training data)
```

---

## 9. Constants

```python
SNAPSHOT_INTERVAL = 5        # Ticks between snapshots
MAX_SNAPSHOTS = 200          # Max snapshots per Memory
MAX_EVENTS = 500             # Max events per Memory
FISSION_OVERLAP = 0.60       # Min overlap for fission detection
PREDICT_WINDOW = 20          # Ticks ahead for death prediction
RETRAIN_INTERVAL = 20        # Ticks between model retraining
LINEAGE_REPORT_INTERVAL = 100  # Ticks between lineage reports
```

---

## 10. New Dependencies

```
scikit-learn>=1.5.0
```

---

## 11. Success Criteria

1. Fission detection correctly identifies >= 80% of true fission events (manual validation on 50 cases)
2. At least 3 lineages reach depth >= 3 generations
3. Survival analysis produces statistically significant trend (p < 0.05 on lifespan vs generation)
4. Death Predictor accuracy >= 0.65 on held-out lifecycles
5. At least one shape_hash appears in >= 3 consecutive generations
6. All existing 90 tests continue to pass

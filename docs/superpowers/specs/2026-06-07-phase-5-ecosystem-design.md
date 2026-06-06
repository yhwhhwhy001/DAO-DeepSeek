# Phase 5: Ecosystem Emergence Design Spec

> **Status:** Draft | **Date:** 2026-06-07

## 1. Overview

**Goal:** Transform the uniform universe into a heterogeneous ecosystem with spatial resource gradients, emergent resource dynamics, and automatically detected ecological relationships (competition, mutualism, predation, symbiosis).

**Approach:** One environmental rule (solar gradient: top half gets 1.5x energy injection, bottom half 0.5x). Cell death creates energy remnants that persist and can be absorbed. Ecology Engine scans structures every 50 ticks, detects pairwise relationships, and builds an ecological network graph.

**Validation:** At least 1 competition pair and 1 mutualism pair detected within 500 ticks; energy remnants create measurable spatial heterogeneity; ecological network has >= 3 nodes and >= 2 edge types.

---

## 2. Map Engine — Solar Gradient

### 2.1 Rule

```
Grid divided into two regions by the y-midpoint:

  Top half (y < height/2):   energy_multiplier = 1.5
  Bottom half (y >= height/2): energy_multiplier = 0.5

Injection modified:
  Each injection tick: energy_input × N random positions
  Each position receives +1.0 × multiplier energy
  So top half gets ~3x more energy per position than bottom half
```

### 2.2 No Other Presets

All other heterogeneity emerges from cell activity. No terrain types, no predefined patches, no designed resource distributions.

---

## 3. Resource Engine — Energy Remnants

### 3.1 Remnant Creation

```
When a cell dies (energy <= 0 from decay):
  remnant = EnergyRemnant(
    position = (cell.x, cell.y),
    energy = cell.energy_before_decay × 0.5,
    type = cell.type,
    decay_rate = 0.05,     # remnants slowly fade
  )
  Grid stores remnants alongside cells (separate layer)
```

### 3.2 Remnant Absorption

```
When new cell is born at position (injection or fission):
  If remnant exists at position:
    cell.energy += remnant.energy × absorption_efficiency(cell.type, remnant.type)
    Remove remnant

When cell MOVES to a position with remnant:
  cell.energy += remnant.energy × 0.5 × absorption_efficiency(cell.type, remnant.type)
  remnant.energy ×= 0.5  # half remains for next visitor

Absorption efficiency matrix:
           Remnant type
           0    1    2    3
Cell  0   1.0  0.3  0.3  0.3
type  1   0.7  0.7  0.7  0.7
      2   1.5  0.2  1.5  0.2
      3   0.8  0.8  0.8  0.8

Type 0: specialist (prefers own type)
Type 1: generalist (moderate all)
Type 2: specialist (strong on own and 2, weak on 1 and 3)
Type 3: opportunist (equal moderate efficiency)
```

### 3.3 Remnant Decay

```
Each tick:
  For each remnant:
    remnant.energy -= remnant.decay_rate
    If remnant.energy <= 0: remove remnant
```

---

## 4. Ecology Engine

### 4.1 Relationship Detection

**Competition:**
```
For each pair of active structures (A, B):
  spatial_overlap = |A.cells ∩ B.cells区域| / min(|A区域|, |B区域|)
  resource_overlap = fraction of same-type remnants exploited by both
  if spatial_overlap > 0.3 OR resource_overlap > 0.5:
    mark competition, strength = spatial_overlap × resource_overlap
```

**Mutualism:**
```
For each pair of DIFFERENT-type structures (A, B):
  A and B are adjacent (spatially near, not overlapping)
  Coexist duration > 50 ticks
  Resource types used DO NOT overlap (< 0.2 resource_overlap)
  mark mutualism, strength = coexistence_ticks / 100
```

**Energy Flow (Predation/Symbiosis):**
```
Track cell movements between structures:
  cell moves from structure A region to B region
  cell's energy is absorbed by B (fusion)
  net_flow_A_to_B accumulates

  if net_flow_A_to_B > 0 and net_flow_B_to_A == 0:
    mark predation (A → B), strength = net_flow / total_energy_A
  if both directions have significant flow (> 20% of total):
    mark symbiosis, strength = min(flow_ratio_A, flow_ratio_B)
```

### 4.2 Ecological Network

```python
EcologyNode:
  structure_id: str
  primary_type: int
  trophic_level: float       # computed from energy flow graph
  niche: str                 # "producer" (creates more energy than consumes)
                             # "consumer" (net energy sink)
                             # "decomposer" (absorbs remnants primarily)
  population: int

EcologyEdge:
  from_id / to_id: str
  relationship: str          # competition / mutualism / predation / symbiosis
  strength: float            # 0-1

EcologyNetwork:
  nodes: dict[str, EcologyNode]
  edges: list[EcologyEdge]
  tick: int
```

### 4.3 Niche Classification

```
Producer:   total_energy_generated (via fission/injection near structure) > total_energy_consumed (via decay)
Consumer:   total_energy_consumed > total_energy_generated
Decomposer: > 50% of energy intake from remnants
```

### 4.4 Output (every 100 ticks)

```
=== Ecology Report (tick 500) ===
Nodes: 12 | Edges: 18

By niche:
  Producers:  5
  Consumers:  4
  Decomposers: 3

Top relationships:
  Competition: s1 ↔ s3 (strength=0.72)
  Mutualism:   s5 ↔ s7 (strength=0.45, 87 ticks)
  Predation:   s2 → s8 (flow=15.3 energy)
  Symbiosis:   s4 ↔ s9 (bidirectional flow)

Food chain found: s1 → s3 → s8 (length=3)
```

---

## 5. Data Model

### 5.1 Energy Remnant

```python
@dataclass
class EnergyRemnant:
    x: int
    y: int
    energy: float
    type: int          # originating cell type
    decay_rate: float = 0.05
```

### 5.2 New Event Types

```
REMNANT_CREATED    {"x": int, "y": int, "energy": float, "type": int}
REMNANT_ABSORBED   {"x": int, "y": int, "energy": float, "cell_id": str}
REMNANT_EXPIRED    {"x": int, "y": int}
```

---

## 6. File Structure

```
src/
  map_engine.py          # Solar gradient, multiplier lookup
  resource_engine.py     # EnergyRemnant CRUD, absorption, decay
  ecology_engine.py      # Relationship detection, EcologyNetwork, reports

tests/
  test_map_engine.py
  test_resource_engine.py
  test_ecology_engine.py

src/state_engine.py      # MODIFY: injection uses multiplier, death creates remnants
src/event_bus.py         # MODIFY: REMNANT_CREATED/ABSORBED/EXPIRED
src/cli/renderer.py      # MODIFY: Ecology panel + remnant overlay on grid
run.py                   # MODIFY: wire Phase 5 engines
```

---

## 7. Constants

```python
SOLAR_MULTIPLIER_TOP = 1.5
SOLAR_MULTIPLIER_BOTTOM = 0.5
REMNANT_ENERGY_RATIO = 0.5        # fraction of dead cell energy kept
REMNANT_DECAY_RATE = 0.05         # per tick
REMNANT_ABSORB_MOVE_RATIO = 0.5   # fraction absorbed on move
COMPETITION_SPATIAL_THRESHOLD = 0.3
COMPETITION_RESOURCE_THRESHOLD = 0.5
MUTUALISM_COEXIST_MIN = 50        # ticks
ECOLOGY_SCAN_INTERVAL = 50        # ticks between scans
ECOLOGY_REPORT_INTERVAL = 100     # ticks between reports
```

### Absorption Matrix

```python
ABSORPTION_MATRIX = {
    # cell_type: {remnant_type: efficiency}
    0: {0: 1.0, 1: 0.3, 2: 0.3, 3: 0.3},
    1: {0: 0.7, 1: 0.7, 2: 0.7, 3: 0.7},
    2: {0: 0.2, 1: 0.2, 2: 1.5, 3: 0.2},
    3: {0: 0.8, 1: 0.8, 2: 0.8, 3: 0.8},
}
```

---

## 8. Success Criteria

1. Energy remnants created on cell death and visible in grid visualization
2. Solar gradient produces measurable cell density difference (top vs bottom half, > 20% difference)
3. >= 1 competition pair detected (spatial_overlap > 0.3)
4. >= 1 mutualism pair detected (coexist > 50 ticks, different types)
5. Ecological network has >= 3 nodes and >= 2 different edge types
6. All existing 151 tests continue to pass

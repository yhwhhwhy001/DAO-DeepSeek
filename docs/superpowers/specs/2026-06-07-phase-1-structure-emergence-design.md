# Phase 1: Structure Emergence Design Spec

> **Status:** Draft | **Date:** 2026-06-07

## 1. Overview

**Goal:** Observe stable structures naturally emerging from the Phase 0 universe through automated detection, tracking, pattern recognition, and entropy measurement.

**Approach:** Three-stage pipeline — first build the Structure Detector (the "eyes"), then use it as the objective function for parameter scanning to find interesting parameter regimes, finally add entropy analysis and leaderboard for a complete observation toolkit.

**Validation:** Stable structures (age >= 20 ticks, size variation < 30%) naturally appear without any rule changes.

---

## 2. Structure Detector

### 2.1 Definition

A **Structure** is a spatially connected group of cells that persists across ticks, identified by:

1. **Space:** Cells are 8-connected (Moore neighborhood) in a single tick → `Component`
2. **Time:** Components matched across ticks via dual matching → `Structure`
3. **Stability:** Age >= `STABILITY_AGE` (20) ticks AND size coefficient of variation < `STABILITY_CV` (0.30)

### 2.2 Data Model

```
Component (单 tick 快照):
  id: str                 # "{tick}_{index}" e.g. "42_3"
  cell_ids: set[str]
  centroid: (float, float)
  bbox: (min_x, min_y, max_x, max_y)
  type_counts: dict[int, int]

Structure (跨 tick 实体):
  id: str                 # 继承首个 component.id
  age: int                # 存活 tick 数
  cells: set[str]         # 当前 cell ID 集合
  size_history: list[int] # 最近 N 个 tick 的 cell 数量
  centroid: (float, float)
  shape_hash: str         # 归一化空间模式哈希
  status: "candidate" | "stable" | "dead"
  born_at: int
  last_seen_at: int
  missed_ticks: int       # 连续未匹配 tick 数
```

### 2.3 Dual-Matching Algorithm

```
For each known Structure S (where status != "dead"):
  candidates = all Components in current tick
  sort candidates by |S.cells ∩ C.cell_ids| descending
  
  best = candidates[0]
  cell_overlap = |S.cells ∩ best.cell_ids| / max(|S.cells|, |best.cell_ids|)
  
  if cell_overlap >= 0.50:
    match → update S with best
  else:
    bbox_iou = intersection_area / union_area
    if bbox_iou >= 0.30:
      match → update S with best
    else:
      S.missed_ticks += 1
      
Unmatched Components → new Structure (status="candidate", born_at=tick)
S.missed_ticks >= 3 → status = "dead"
```

### 2.4 Stability Check

Run at each tick for every non-dead Structure:

```
if age >= STABILITY_AGE and size_cv < STABILITY_CV:
  status = "stable"
```

---

## 3. Pattern Hasher

### 3.1 Shape Hash

```
def compute_shape_hash(cell_positions, centroid):
  1. relative = [(x - cx, y - cy) for (x,y) in cell_positions]
  2. quantize each coord to nearest integer
  3. canonical = sorted(relative)  # 字典序
  4. sha256(repr(canonical))[:12]  # 前 12 位 hex
```

Same hash = same spatial pattern, regardless of grid position.

### 3.2 Pattern Registry

```
PatternRegistry:
  patterns: dict[str, PatternRecord]

PatternRecord:
  shape_hash: str
  first_seen: int
  total_occurrences: int
  max_concurrent: int
  locations: list[(int, int)]  # centroid positions, last 20
```

---

## 4. Entropy Engine

### 4.1 Three-Layer Measurement

**Layer 1 — Global Entropy (type diversity of all cells)**
```
H_global = -Σ p(type_i) * log2(p(type_i))
Range: 0 to log2(num_types)
Signal: rising = type diversity increasing; falling = one type dominating
```

**Layer 2 — Local Spatial Entropy (mixing of types)**
```
For each cell: compute H of its 8 neighbors (including self)
H_local = mean(all cell entropies)
Signal: low = types clustering together (structure); high = types mixed (chaos)
```

**Layer 3 — Structure Entropy (pattern diversity)**
```
H_struct = -Σ p(shape_hash) * log2(p(shape_hash))
Computed over all active structures
Signal: low = few patterns dominate; high = many different patterns
```

### 4.2 Trend Signals

Evaluated every `TREND_WINDOW` (50) ticks:
- **Ordering:** local_entropy ↓ AND stable_count ↑
- **Chaos:** local_entropy ↑ AND stable_count ↓
- **Steady:** all metrics within ±5% band
- **Diversifying:** H_global ↑ AND unique_patterns ↑

---

## 5. Leaderboard

### 5.1 Scoring

```
Stability Score  = age / max_age_in_universe
Complexity Score = avg_cell_count / max_cell_count
Diversity Score  = unique_types_in_structure / num_types
Pattern Score    = pattern_occurrences / max_occurrences

Composite = stability*0.35 + complexity*0.25 + diversity*0.25 + pattern*0.15
```

### 5.2 Output

Top-5 structures and top-5 patterns, updated every tick:
- Structure ID, age, size, type count, shape hash, composite score
- Pattern hash, occurrence count, locations

---

## 6. Parameter Scanner

### 6.1 Search Space

| Parameter | Range | Step |
|-----------|-------|------|
| decay_rate | 0.1 – 2.0 | 0.2 |
| drift_probability | 0.0 – 0.2 | 0.05 |
| fission_threshold | 5.0 – 20.0 | 3.0 |
| fusion_probability | 0.0 – 0.05 | 0.01 |
| energy_input | 1 – 20 | 2 |
| num_types | 2 – 6 | 1 |

### 6.2 Two-Stage Process

**Coarse (random sample):** 500 random param sets × 200 ticks → keep top 20% by score

**Fine (grid sweep):** Dense grid around each top-20% candidate × 500 ticks × 3 seeds → final ranking

### 6.3 Objective Function

```
score = stable_structures * 3.0
      + unique_patterns  * 2.0
      + max_age          * 0.1
      + alive_count      * 0.02
```

Maximizes structural richness and longevity.

---

## 7. CLI Layout

```
┌──────────────────────────────────────────────────────────┐
│  DAO Genesis — Phase 1                          Tick: 423│
├───────────────────────────┬──────────────────────────────┤
│                           │  Entropy                     │
│     Universe Grid         │  Global:  1.82 bits          │
│     (80×40, as before)    │  Local:   0.94 ± 0.23        │
│                           │  Struct:  2.15 bits          │
│                           │  Trend:   Ordering ↑         │
│                           ├──────────────────────────────┤
│                           │  Structures (5 total/3 stable)│
│                           │  1. tick42_3  age=156 sz=12  │
│                           │  2. tick51_1  age=87  sz=8   │
│                           │  3. tick89_2  age=45  sz=15  │
│                           ├──────────────────────────────┤
│                           │  Event Log (last 6)          │
│                           │  + a3f2 @(12,34) t=2         │
│                           │  - b1c4 (decay)              │
├───────────────────────────┴──────────────────────────────┤
│  Alive: 47 | Energy: 156.3 | Structures: 5(3) | Ptrns: 2│
└──────────────────────────────────────────────────────────┘
```

---

## 8. File Structure

```
src/
  structure_detector.py    # Component extraction, structure tracking, dual matching
  pattern_hasher.py        # Shape hash, pattern registry
  entropy_engine.py        # 3-layer entropy, trend detection
  leaderboard.py           # 4-dim ranking, composite scoring
  parameter_scanner.py     # Coarse + fine scan, result export

tests/
  test_structure_detector.py
  test_pattern_hasher.py
  test_entropy_engine.py
  test_leaderboard.py

experiments/
  phase1_scan.yaml         # Scanner configuration

run.py                     # Updated layout with Phase 1 panels
```

### Module Dependencies

```
structure_detector → grid, cell
pattern_hasher     → structure_detector (reads shape_hash)
entropy_engine     → grid, structure_detector
leaderboard        → structure_detector, pattern_hasher
parameter_scanner  → world_engine, structure_detector, entropy_engine
```

### EventBus Integration

New event types for Phase 1:
```
STRUCTURE_FORMED     {"structure_id": str, "component_id": str, "cell_count": int}
STRUCTURE_LOST       {"structure_id": str, "age": int, "reason": str}
STRUCTURE_STABLE     {"structure_id": str, "age": int, "shape_hash": str}
TREND_CHANGED        {"previous": str, "current": str}
```

---

## 9. Constants

```python
STABILITY_AGE = 20        # Min ticks for stability
STABILITY_CV  = 0.30      # Max size coefficient of variation
CELL_OVERLAP  = 0.50      # Min Jaccard for cell-ID match
BBOX_IOU      = 0.30      # Min IoU for position fallback
MISSED_MAX    = 3         # Consecutive misses → dead
TREND_WINDOW  = 50        # Ticks per trend evaluation
SHAPE_HASH_LEN = 12       # Hex chars of SHA256 prefix

COARSE_SAMPLES  = 500
COARSE_TICKS    = 200
COARSE_TOP_PCT  = 0.20
FINE_TICKS      = 500
FINE_SEEDS      = 3
```

---

## 10. Success Criteria (MVP for Phase 1)

1. Structure Detector correctly extracts connected components each tick
2. Dual matching tracks structures across ticks with < 5% false positive rate
3. At least 3 parameter sets from the coarse scan produce >= 1 stable structure
4. Entropy Engine produces valid (non-constant) measurements for all 3 layers
5. CLI displays the updated two-column layout with leaderboard
6. All unit tests pass

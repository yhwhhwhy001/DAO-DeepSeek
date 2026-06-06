# Phase 4: Digital Life Emergence Design Spec

> **Status:** Draft | **Date:** 2026-06-07

## 1. Overview

**Goal:** Automatically identify lifeforms in the running universe by computing a 5-dimension Life Score (Survival, Memory, Replication, Decision, Adaptation) for each active structure, then classifying them as proto-lifeform (>=60) or true-lifeform (>=80).

**Approach:** A single LifeDetector module that consumes existing data from StructureDetector (stability), MemoryEngine (snapshots/events/lineage), and DecisionEngine (Q-table/action history). Scores computed every 10 ticks per structure with age >= 10. Emits LIFEFORM_DETECTED, LIFEFORM_ADVANCED, LIFEFORM_LOST events.

**Validation:** At least 1 proto-lifeform detected within 500 ticks, all 5 dimension scores verified on 5 manual samples, events trigger correctly.

---

## 2. Life Score Computation

### 2.1 Survival Score (0-20)

```
age_norm = min(age / 100, 1.0)
score = age_norm * 10
if structure.status == "stable": score += 5
score += min(generation, 5)  # lineage depth bonus
clamp to [0, 20]
```

### 2.2 Memory Score (0-20)

```
snapshot_ratio = min(snapshot_count / 50, 1.0)
event_types = len(set(e.event_type for e in memory.events))
event_diversity = event_types / 5
score = snapshot_ratio * 8 + event_diversity * 6
if memory.parent_id is not None and len(memory.fission_children) > 0:
    score += 6  # lineage completeness
clamp to [0, 20]
```

### 2.3 Replication Score (0-20)

```
children = len(memory.fission_children)
score = min(children / 5, 1.0) * 12
if memory.lineage_root:
    max_gen = max generation among all structures with same lineage_root
    score += min(max_gen / 3, 1.0) * 8
clamp to [0, 20]
```

### 2.4 Decision Score (0-20)

Requires DecidingCell from DecisionEngine:
```
total = total_actions_recorded
non_stay = non_stay_actions
non_stay_ratio = non_stay / max(total, 1)
q_entries = len(utility._q_table)
unique_actions = len(set(action_history))

score = non_stay_ratio * 10
score += min(q_entries / 20, 1.0) * 6
score += min(unique_actions / 5, 1.0) * 4
clamp to [0, 20]
```

### 2.5 Adaptation Score (0-20)

```
if snapshots >= 5:
    energies = [s.total_energy for s in memory.snapshots[-20:]]
    energy_cv = std(energies) / mean(energies) if mean > 0 else 1.0
    score = (1.0 - min(energy_cv, 1.0)) * 10

    # Recovery speed: ticks from near_death to safe (energy > 1.0)
    recovery_events = [e for e in memory.events if e.event_type == "near_death"]
    if recovery_events:
        avg_recovery = avg ticks between near_death and next energy > 1.0
        score += max(6 - avg_recovery / 5, 0)  # faster = higher
    else:
        score += 6  # no near death = perfect

    # Homeostasis: energy_trend close to 0
    energy_trend = slope of last 10 energy values
    if abs(energy_trend) < 0.1: score += 4
    elif abs(energy_trend) < 0.3: score += 2
else:
    score = 10  # neutral baseline for young structures

clamp to [0, 20]
```

### 2.6 Classification

```
total = survival + memory + replication + decision + adaptation
total >= 80 → "true-lifeform"
total >= 60 → "proto-lifeform"
otherwise   → "inert"
```

---

## 3. Life Detector

### 3.1 Data Model

```
LifeAssessment:
  structure_id: str
  tick: int
  scores: dict[str, float]  # survival, memory, replication, decision, adaptation
  total_score: float
  classification: str

LifeformRecord:
  structure_id: str
  first_detected_at: int | None
  first_true_at: int | None
  peak_score: float = 0
  peak_tick: int = 0
  assessments: list[LifeAssessment]  # last 20
  status: str  # "alive" | "dead"
```

### 3.2 Event Types

```
LIFEFORM_DETECTED   {"structure_id": str, "score": float, "classification": str}
LIFEFORM_ADVANCED   {"structure_id": str, "old_class": str, "new_class": str, "score": float}
LIFEFORM_LOST       {"structure_id": str, "peak_score": float, "lifespan": int}
```

### 3.3 Lifecycle

```
Every 10 ticks:
  For each active structure (age >= 10):
    Compute 5 dimension scores
    Classify
    If first time reaching proto-lifeform: emit LIFEFORM_DETECTED
    If promoted from proto to true: emit LIFEFORM_ADVANCED
    Update LifeformRecord

On STRUCTURE_LOST:
  If was a lifeform: emit LIFEFORM_LOST, mark status="dead"
```

---

## 4. CLI

```
Life panel (right column, below Decision):
  Proto-lifeforms: N
  True lifeforms: M
  Top 3 lifeforms by score:
    #1 structure_id  score=XX.X  class=true-lifeform
    #2 structure_id  score=XX.X  class=proto-lifeform

Footer:
  Life: M True, N Proto | Top: structure_id (score)
```

---

## 5. File Structure

```
src/
  life_detector.py       # LifeDetector: scoring + classification + tracking

tests/
  test_life_detector.py

src/event_bus.py         # MODIFY: add LIFEFORM_DETECTED/ADVANCED/LOST
src/cli/renderer.py      # MODIFY: Life panel
run.py                   # MODIFY: wire LifeDetector
```

---

## 6. Success Criteria

1. >= 1 proto-lifeform (score >= 60) detected within 500 ticks
2. All 5 dimension scores verified correct on 5 manual structure samples
3. LIFEFORM_DETECTED and LIFEFORM_ADVANCED events fire correctly
4. All 143 existing tests continue to pass

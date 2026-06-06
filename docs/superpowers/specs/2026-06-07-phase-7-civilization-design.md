# Phase 7: Civilization Layer Design Spec

> **Status:** Draft | **Date:** 2026-06-07

## 1. Overview

**Goal:** Detect civilizations — persistent clusters of lineages sharing symbols and mutualistic relationships — and record their multi-layered history and mythic narratives.

**Approach:** Civilization Engine uses Louvain community detection on the Ecology Network, filtered by lineage diversity, shared symbols, and mutualism. History Engine records events at three levels (individual, communal, environmental). Myth Engine generates founder narratives, hero lineages, and belief systems from knowledge items.

**Validation:** >= 1 civilization detected; >= 1 civilization event per type; myth narrative generated for detected civilization.

---

## 2. Civilization Engine

### 2.1 Detection Algorithm

```
Every 100 ticks:

1. Build community graph from EcologyNetwork:
   Nodes: active structures
   Edge weight = Σ mutualism_strength + Σ (1 - competition_strength)

2. Louvain community detection → natural clusters

3. Filter candidates:
   distinct_lineage_roots >= 3
   shared_symbols >= 2 (symbols present in >= 50% of members)
   mutualism_edges >= 1 within cluster
   total_population >= 10

4. Core detection:
   Node with highest degree centrality → civilization core
   Core's lineage_root → founder_lineage

5. Cross-tick matching:
   lineage_overlap = |old ∩ new| / |old ∪ new|
   overlap >= 0.5 → same civilization, update
   overlap < 0.5 but >= 2 shared lineages → branch (parent-child split)
   otherwise → new civilization
```

### 2.2 Data Model

```
Civilization:
  id: str
  member_lineages: list[str]
  member_structures: list[str]
  core_structure_id: str
  founder_lineage: str
  born_at: int
  died_at: int | None
  peak_size: int
  peak_tick: int
  status: "emerging" | "expanding" | "stable" | "declining" | "fallen"
  shared_symbols: list[str]
  dominant_channel: int
  era: str
```

### 2.3 Events

```
CIVILIZATION_BORN       {"civilization_id": str, "founder": str, "size": int}
CIVILIZATION_EXPANDED   {"civilization_id": str, "new_lineage": str, "size": int}
CIVILIZATION_CONTRACTED {"civilization_id": str, "lost_lineage": str, "size": int}
CIVILIZATION_FALLEN     {"civilization_id": str, "peak_size": int, "lifespan": int}
```

---

## 3. History Engine

### 3.1 Three-Layer Recording

**Individual History (per lineage):**
```
LineageHistory:
  lineage_root: str
  born_tick: int
  died_tick: int | None
  max_generation: int
  total_structures: int
  key_events: list[HistoryEvent]
    HistoryEvent: tick, event_type ("founded"/"peak"/"decline"/"extinction"), data
```

**Communal History (per civilization):**
```
CivilizationHistory:
  civilization_id: str
  timeline: list[EraEvent]
    EraEvent: tick_range, era_name, size_range, key_development
  member_histories: list[LineageHistory]
```

**Environmental History (per region):**
```
EnvironmentalHistory:
  region: str  # "top" / "bottom" (solar gradient zones)
  resource_timeline: list[(tick, remnant_count, cell_density)]
  civilization_presence: list[(tick, civilization_ids)]
```

### 3.2 Era Detection

```
Based on civilization size_trajectory:
  Consecutive growth >= 3 scans → "expanding" era
  Size within 10% of peak → "golden_age" era
  Consecutive decline >= 3 scans → "declining" era
  First scan → "founding" era
```

---

## 4. Myth Engine

### 4.1 Founder Narrative

Auto-generated per civilization:
```
"{civilization_name} was founded by {founder_lineage} at tick {born_at}
 in the {region} region. It rose amidst {competitor_count} rivals
 and formed {mutualism_count} alliances. At its peak (tick {peak_tick}),
 it encompassed {peak_size} lineages with {peak_cells} cells."
```

### 4.2 Hero Lineage

```
For each civilization:
  Rank member lineages by: peak_score + knowledge_transmission_depth + symbol_count
  Top lineage → "Hero"
  
  Hero narrative:
    "Lineage {root} was the greatest of {civ_name}. It discovered {knowledge_count}
     truths, spoke through channel {channel}, and its bloodline reached generation {max_gen}.
     Its fall came at tick {died_at} after {lifespan} ticks of glory."
```

### 4.3 Belief System

```
For each civilization:
  Collect all Knowledge items with generation_depth >= 3 within member lineages
  These form the civilization's "tenets"

  Tenet:
    knowledge_id: str
    formulation: "{antecedent} leads to {consequent}"
    confidence: float
    believer_count: int (lineages holding this knowledge)
    first_seen / last_seen: int

  Rank tenets by: believer_count × confidence × generation_depth
  Top 3 → "Core Beliefs"
  Rest → "Folk Knowledge"
```

---

## 5. CLI

```
Civilization panel (right column, between Cognition and Ecology):
  Civilizations: N active (M fallen)
  Top civ: civ_N (size=X, era=golden_age)
  Hero lineage: root_Y (generation=Z)
  Core beliefs: 3 tenets

Footer update:
  Civs: N active | Top: civ_N (X lineages, era)
```

---

## 6. File Structure

```
src/
  civilization_engine.py   # Community detection + civilization tracking
  history_engine.py        # Three-layer event recording + era detection
  myth_engine.py           # Narrative generation + hero/belief extraction

tests/
  test_civilization_engine.py
  test_history_engine.py
  test_myth_engine.py

src/event_bus.py           # MODIFY: CIVILIZATION_BORN/EXPANDED/CONTRACTED/FALLEN
src/cli/renderer.py        # MODIFY: Civilization panel
run.py                     # MODIFY: wire Phase 7 engines
```

---

## 7. Constants

```
CIV_SCAN_INTERVAL = 100
CIV_MIN_LINEAGES = 3
CIV_MIN_SHARED_SYMBOLS = 2
CIV_MIN_MUTUALISM = 1
CIV_MIN_POPULATION = 10
CIV_OVERLAP_THRESHOLD = 0.5
ERA_GROWTH_SCANS = 3
ERA_DECLINE_SCANS = 3
BELIEF_MIN_DEPTH = 3
```

---

## 8. Success Criteria

1. >= 1 civilization detected within 1000 ticks
2. >= 1 event of each type (BORN, EXPANDED, CONTRACTED, FALLEN) emitted
3. Myth Engine generates valid founder narrative for detected civilization
4. >= 1 hero lineage identified with non-empty narrative
5. All existing 181 tests continue to pass

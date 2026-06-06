# Phase 6: Cognition Layer Design Spec

> **Status:** Draft | **Date:** 2026-06-07

## 1. Overview

**Goal:** Build three new engines that together form a cognition pipeline — Symbol Engine (clusters Q-table states into symbols), Knowledge Engine (discovers causally-verified cross-lineage knowledge), and Language Engine (enables inter-cell communication via composite SIGNAL carrying symbol sequences).

**Approach:** Symbols emerge from clustering Q-table state keys by bucket similarity. Knowledge emerges from symbol co-occurrence patterns validated across >= 2 independent lineages. Language uses enhanced SIGNAL with channel + symbol sequence to create cross-cell symbol associations.

**Validation:** >= 5 symbols discovered; >= 1 knowledge validated across >= 2 lineages; symbol transmission rate > 0 via SIGNAL; at least 1 symbol persists across >= 3 generations.

---

## 2. Symbol Engine

### 2.1 Clustering

```
Every 50 ticks:
  Collect all (state_key, action) pairs from all DecidingCell Q-tables
    where |Q(s,a)| > 0.1
  Build adjacency: two state_keys are similar if
    >= 5 of 7 discretize dimensions have the same bucket value
  Single-linkage clustering with threshold 5/7
  Each cluster → a Symbol
```

### 2.2 Symbol Data Model

```
Symbol:
  id: str                  # "sym_N"
  centroid_state: str      # representative state_key
  dominant_action: str     # most common action in cluster
  cell_count: int          # cells using this symbol
  lineage_count: int       # distinct lineages using this symbol
  first_seen: int          # tick first discovered
  last_seen: int           # tick last observed
  parent_symbols: list[str]  # symbols this evolved from
```

### 2.3 Symbol Evolution

```
Each scan:
  Match clusters to previous scan's symbols by Jaccard overlap
  Overlap > 0.6 → same symbol, update
  Overlap < 0.4:
    If old symbol splits into 2+ new clusters → "differentiated"
    If entirely new cluster → "emerged"
  Symbol lineage_count >= 2 → "convergent symbol" (independently evolved)
```

---

## 3. Knowledge Engine

### 3.1 Knowledge Discovery

```
Every 50 ticks:
  For each cell's Q-table access sequence (state_key timeline):
    Find symbol transitions: sym_A → sym_B
    where sym_A.dominant_action != "STAY"
    and sym_A appears before sym_B in time

  Keep candidates with co-occurrence >= 5

  Causal test:
    lift = P(sym_B | sym_A) / P(sym_B)
    if lift > 1.5 → pass

  Lineage cross-validation:
    Candidate must appear in >= 2 independent lineages
    In each: P(sym_B|sym_A) > 1.2

  Pass → Knowledge
```

### 3.2 Knowledge Data Model

```
Knowledge:
  id: str                  # "know_N"
  antecedent: str          # sym_A id
  consequent: str          # sym_B id
  confidence: float        # lift ratio
  lineage_count: int       # validating lineages
  survival_effect: float   # relative lifespan of cells using this knowledge
  generation_depth: int    # max generations this knowledge survived
  first_seen: int
  status: "ephemeral" | "stable" | "persistent"  # persistent >= 3 gens
```

---

## 4. Language Engine

### 4.1 Enhanced SIGNAL

```
SIGNAL action redefined:
  Outgoing:
    signal = {
      channel: int (0-3),
      symbols: [str, str, str],  # last 3 symbols used by sender
    }
    Cost: 0.3 energy
    Broadcast to 8-neighbors

  Incoming:
    Receiving cell:
      Filter by genetic rule: channel_preference (which channel to listen to)
      For each received symbol:
        If cell's current symbol matches antecedent of a Knowledge:
          Reinforce Q(current_state, consequent_symbol.dominant_action)
      Track: signals_received count for reward
```

### 4.2 Communication Statistics

```
Every 100 ticks:
  Symbol send counts (most transmitted symbols)
  Cross-lineage vs within-lineage communication ratio
  Behavioral change rate: % of signals received that led to action change
  Channel usage distribution
```

---

## 5. CLI

```
Cognition panel (below Ecology):
  Symbols: N active (M convergent)
  Knowledge: K items (P persistent)
  Language: S signals/tick, X% cross-lineage
  Top symbol: sym_N (dominant_action=MOVE_*, cell_count=Y)
  Top knowledge: sym_A → sym_B (confidence=Z, gen_depth=W)
```

---

## 6. File Structure

```
src/
  symbol_engine.py       # Q-table clustering + symbol tracking
  knowledge_engine.py    # symbol co-occurrence + lineage validation
  language_engine.py     # enhanced SIGNAL + communication stats

tests/
  test_symbol_engine.py
  test_knowledge_engine.py
  test_language_engine.py

src/action_engine.py     # MODIFY: SIGNAL cost/definition
src/decision_engine.py   # MODIFY: SIGNAL handling in step_all
src/cli/renderer.py      # MODIFY: Cognition panel
run.py                   # MODIFY: wire Phase 6 engines
```

---

## 7. Constants

```python
SYMBOL_SCAN_INTERVAL = 50
Q_VALUE_THRESHOLD = 0.1
STATE_SIMILARITY_THRESHOLD = 5  # out of 7 dimensions
CLUSTER_OVERLAP_THRESHOLD = 0.6
KNOWLEDGE_COOCCUR_MIN = 5
KNOWLEDGE_LIFT_THRESHOLD = 1.5
KNOWLEDGE_LINEAGE_MIN = 2
KNOWLEDGE_PERSISTENT_GENS = 3
SIGNAL_CHANNELS = 4
SIGNAL_SYMBOL_COUNT = 3
```

---

## 8. Success Criteria

1. >= 5 symbols discovered within 500 ticks
2. >= 1 convergent symbol (lineage_count >= 2)
3. >= 1 knowledge validated across >= 2 lineages
4. > 0 signals transmitted via Language Engine
5. >= 1 symbol persists across >= 3 generations
6. All existing 168 tests continue to pass

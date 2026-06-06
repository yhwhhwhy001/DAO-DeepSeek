# Phase 3: Decision Emergence Design Spec

> **Status:** Draft | **Date:** 2026-06-07

## 1. Overview

**Goal:** Give each cell a decision-making capability — sense its environment, choose from 13 possible actions via genetic rules + Q-learning, and learn from outcomes. Observe whether "approach benefit, avoid harm" behavior emerges naturally.

**Approach:** Three new engines (Condition, Action, Utility) operate per-cell each tick. Actions modulate existing physics probabilities rather than replacing them. Genetic rules provide innate tendencies; Q-learning provides experiential adaptation. Both are inherited with variation during fission.

**Validation:** >= 30% cells take non-STAY actions; >= 2 rules persist across >= 2 generations; Q-using cells outlive non-Q cells; "avoid hostile" rule appears naturally in top 5.

---

## 2. Condition Engine

### 2.1 State Vector (10 dimensions)

```
Spatial (4):
  local_energy_density:  mean energy of 8-neighbors (0 if none)
  same_type_ratio:       fraction of neighbors with same type
  hostile_type_ratio:    fraction of neighbors with different type
  empty_slots:           count of empty neighbor positions

Self (4):
  energy_level:          energy / max_energy_observed (clamped to [0,1])
  energy_trend:          slope of energy over last 5 ticks (-1, 0, +1 bucketed)
  generation:            generation number from Memory
  age_normalized:        age / mean_age_of_same_type

Structure (2):
  structure_size:        number of cells in belonging Structure (0 if none)
  structure_stable:      1 if Structure.status == "stable", else 0
```

### 2.2 Discretization for Q-table

| Field | Buckets | Values |
|-------|---------|--------|
| energy_level | 3 | low, mid, high |
| hostile_ratio | 3 | low, mid, high |
| energy_trend | 3 | down, flat, up |
| same_type_ratio | 3 | low, mid, high |
| empty_slots | 3 | few, some, many |
| structure_size | 2 | small, large |
| generation | 2 | founder, descendant |
| others | 2 | each |

Total discrete states: 3^5 × 2^3 = 1944. Q-table capped at 200 entries (LRU eviction).

---

## 3. Action Engine

### 3.1 Action Set (13 actions)

| Action | Cost | Effect |
|--------|------|--------|
| MOVE_{N,S,E,W,NE,NW,SE,SW} (8) | 0.5 energy | Move to adjacent empty position |
| STAY (1) | 0 | Remain in place |
| SPLIT (1) | fission_threshold/2 energy | Trigger controlled fission |
| MERGE_REQUEST (1) | 0.2 energy | Request fusion with adjacent same-type cell |
| TYPE_SHIFT (1) | 1.0 energy | Change to most common neighbor type |
| SIGNAL (1) | 0.3 energy | Broadcast state to 8-neighbors |

### 3.2 Decision Algorithm

```
For each cell each tick:

1. Compute state vector S from Condition Engine
2. Compute rule_weight for each action:
     For each rule in cell.rule_set:
       if rule matches S:
         action_weight[rule.action] += rule.weight
3. Compute Q_weight for each action:
     state_key = discretize(S)
     Q_weight[a] = Q.get(state_key, {}).get(a, 0.0)
4. Composite:
     composite[a] = rule_weight[a] * RULE_FACTOR + Q_weight[a] * Q_FACTOR
5. Softmax selection:
     temperature = 0.5 (exploration rate, decays over cell lifetime)
     P(a) = exp(composite[a] / temperature) / Σ exp(...)
6. Sample action from P(a)
7. Execute action (modulate physics, not replace)
```

### 3.3 Physics Modulation (existing rules remain)

```
Drift:   base_prob * (1.0 + drift_modulation from TYPE_SHIFT action)
Fission: base_trigger * (1.0 + fission_modulation from SPLIT action)
Fusion:  base_prob * (1.0 + fusion_modulation from MERGE_REQUEST action)
Action:  always executed (MOVE, STAY, SIGNAL are additive)

If action == MOVE_X and target empty:
  move cell to new position (subtract action cost)
If action == SIGNAL:
  neighbors receive signal event (for condition engine next tick)
```

---

## 4. Genetic Rules

### 4.1 Data Model

```
RuleSet:
  rules: list[Rule]  (3-6 rules at birth)

Rule:
  condition_field: str     # from state vector
  condition_op: ">" | "<"
  condition_value: float
  action: str              # action name
  weight: float            # [-5.0, 5.0]
```

### 4.2 Inheritance with Mutation

```
During fission, child cell inherits parent's RuleSet:

For each rule in inherited set:
  20% chance: condition_value += N(0, 0.1)
  20% chance: weight += N(0, 0.5)
  clamp weight to [-5, 5]

10% chance: add a new random rule
5% chance: drop a random rule

If child ends up with < 2 rules: add random rules until >= 2
If child ends up with > 8 rules: drop random rules until <= 8
```

---

## 5. Utility Engine (Q-Learning)

### 5.1 Reward Function

```
r_t =   0.1                           (survival bonus per tick)
      + energy_delta * 2.0            (energy gain/loss, weighted)
      + 0.5 if structure_size grew    (joined larger structure)
      - 0.3 if structure lost         (structure dissolved)
      + 1.0 if recovered_from_near_death (energy was <0.5, now >1.0)
      + 0.2 per signal_received       (received neighbor signals)
```

### 5.2 SARSA Update

```
δ = r_{t+1} + γ * Q(s_{t+1}, a_{t+1}) - Q(s_t, a_t)
Q(s_t, a_t) += α * δ

α = 0.1, γ = 0.9
```

### 5.3 Q-Table Management

```
Max 200 state entries per cell
Overflow: evict least-recently-used state entry
Only store a state if |Q(s,a)| > 0.01 for any action

Inheritance during fission:
  Child receives parent's Q-table
  Each Q-value multiplied by 0.5 (discount inherited experience)
  Top 50 most-used entries passed
  If parent has < 10 state entries: child starts with empty Q-table
```

---

## 6. Rule Evolution Tracker

```
RuleEvolutionTracker:
  Tracks rule prevalence and persistence across lineages

Every 100 ticks:
  Top 5 rules by survival rate of cells possessing them
  Conservative rules: unchanged across >= 3 generations
  Emerging rules: first appearance in current or previous generation
  Rule-lifespan correlation: which rules predict longer cell life?
```

---

## 7. Constants

```python
RULE_WEIGHT_FACTOR = 0.6
Q_WEIGHT_FACTOR = 0.4
TEMPERATURE_INITIAL = 0.5
TEMPERATURE_DECAY = 0.99  # per tick
ALPHA = 0.1  # learning rate
GAMMA = 0.9  # discount factor
MAX_Q_STATES = 200
Q_INHERIT_DECAY = 0.5
MAX_Q_INHERIT = 50
MIN_Q_INHERIT = 10
RULE_MUTATION_PROB = 0.20
RULE_ADD_PROB = 0.10
RULE_DROP_PROB = 0.05
MIN_RULES = 2
MAX_RULES = 8
```

---

## 8. File Structure

```
src/
  condition_engine.py     # State vector computation + discretization
  ruleset.py              # Rule, RuleSet dataclasses + mutation logic
  action_engine.py        # Action definitions + rule evaluation + softmax selection
  utility_engine.py       # Q-table, SARSA update, reward computation, inheritance
  rule_evolution.py       # Rule prevalence, persistence, correlation analysis

tests/
  test_condition_engine.py
  test_ruleset.py
  test_action_engine.py
  test_utility_engine.py
  test_rule_evolution.py

src/cli/renderer.py       # MODIFY: Decision panel
src/structure_detector.py # MODIFY: SPLIT action integrates with fission
run.py                    # MODIFY: wire Phase 3 engines
```

---

## 9. Success Criteria

1. >= 30% of cells execute non-STAY actions in a given tick
2. >= 2 rules persist across >= 2 generations without change
3. Mean lifespan of Q-using cells > mean lifespan of non-Q cells
4. At least one "avoid threat" type rule appears in top-5 surviving rules
5. All 113 existing tests continue to pass

# Phase 3: Decision Emergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Give each cell a decision-making pipeline — environment sensing, 13-action choice via genetic rules + Q-learning, and outcome-based learning — running as a new DECISION phase in the tick loop.

**Architecture:** Four new modules (ruleset, condition_engine, action_engine, utility_engine) plus a rule_evolution tracker. A new Decision Engine integrates them and runs per-cell each tick before physics rules. Actions modulate physics probabilities or execute directly (MOVE/SIGNAL).

**Tech Stack:** Python 3.14, numpy, rich, PyYAML, scikit-learn (same as Phase 2)

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

## File Structure

```
src/
  ruleset.py              # NEW: Rule, RuleSet dataclasses + mutation
  condition_engine.py     # NEW: 10-dim state vector + discretization
  action_engine.py        # NEW: 13 actions + rule eval + softmax
  utility_engine.py       # NEW: Q-table + SARSA + reward + inheritance
  decision_engine.py      # NEW: per-cell decision pipeline (orchestrator)
  rule_evolution.py       # NEW: rule prevalence/persistence analysis
  time_engine.py          # MODIFY: add DECISION phase before physics

tests/
  test_ruleset.py
  test_condition_engine.py
  test_action_engine.py
  test_utility_engine.py
  test_decision_engine.py
  test_rule_evolution.py

src/cli/renderer.py       # MODIFY: Decision panel
src/structure_detector.py # MODIFY: SPLIT action integration
run.py                    # MODIFY: wire Phase 3 engines
```

---

### Task 1: RuleSet & Rule Dataclasses

**Files:**
- Create: `src/ruleset.py`
- Create: `tests/test_ruleset.py`

- [ ] **Step 1: Write tests/test_ruleset.py**

```python
"""Tests for RuleSet."""
from src.ruleset import Rule, RuleSet, mutate_rule, mutate_ruleset, generate_random_ruleset


class TestRule:
    def test_rule_evaluation(self):
        r = Rule(condition_field="hostile_ratio", condition_op=">", condition_value=0.5,
                 action="MOVE_N", weight=3.0)
        assert r.matches({"hostile_ratio": 0.7}) is True
        assert r.matches({"hostile_ratio": 0.3}) is False
        assert r.matches({}) is False

    def test_rule_mutation(self):
        import random
        rng = random.Random(42)
        r = Rule("energy_level", "<", 0.3, "SPLIT", 2.0)
        original_value = r.condition_value
        original_weight = r.weight
        # Force many mutations
        for _ in range(100):
            mutate_rule(r, rng, value_prob=1.0, weight_prob=1.0)
        # Should have changed
        assert r.condition_value != original_value or r.weight != original_weight

    def test_weight_clamped(self):
        import random
        rng = random.Random(42)
        r = Rule("energy_level", "<", 0.3, "SPLIT", 4.9)
        for _ in range(50):
            mutate_rule(r, rng, value_prob=0.0, weight_prob=1.0)
        assert -5.0 <= r.weight <= 5.0


class TestRuleSet:
    def test_generates_random_ruleset(self):
        import random
        rng = random.Random(42)
        rs = generate_random_ruleset(rng)
        assert 3 <= len(rs.rules) <= 6

    def test_all_rules_have_valid_actions(self):
        import random
        rng = random.Random(42)
        valid_actions = {"MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W", "STAY", "SPLIT",
                         "MERGE_REQUEST", "TYPE_SHIFT", "SIGNAL"}
        rs = generate_random_ruleset(rng)
        for r in rs.rules:
            assert r.action in valid_actions

    def test_mutate_ruleset(self):
        import random
        rng = random.Random(42)
        parent = generate_random_ruleset(rng)
        original_count = len(parent.rules)
        child = mutate_ruleset(parent, rng)
        # Count should stay within [2,8]
        assert 2 <= len(child.rules) <= 8
        # Should be somewhat similar but not identical
        # (some mutations likely happened)
        assert len(child.rules) >= 2
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_ruleset.py -v
```

- [ ] **Step 3: Write src/ruleset.py**

```python
"""RuleSet — genetic if-then rules for cell decision-making."""
import random
from dataclasses import dataclass, field

VALID_ACTIONS = {
    "MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W",
    "MOVE_NE", "MOVE_NW", "MOVE_SE", "MOVE_SW",
    "STAY", "SPLIT", "MERGE_REQUEST", "TYPE_SHIFT", "SIGNAL",
}

VALID_CONDITION_FIELDS = {
    "local_energy_density", "same_type_ratio", "hostile_type_ratio",
    "empty_slots", "energy_level", "energy_trend", "generation",
    "age_normalized", "structure_size", "structure_stable",
}

RULE_MUTATION_PROB = 0.20
RULE_ADD_PROB = 0.10
RULE_DROP_PROB = 0.05
MIN_RULES = 2
MAX_RULES = 8


@dataclass
class Rule:
    condition_field: str
    condition_op: str       # ">" or "<"
    condition_value: float
    action: str
    weight: float

    def matches(self, state: dict) -> bool:
        val = state.get(self.condition_field)
        if val is None:
            return False
        if self.condition_op == ">":
            return val > self.condition_value
        elif self.condition_op == "<":
            return val < self.condition_value
        return False


def mutate_rule(rule: Rule, rng: random.Random, value_prob: float = RULE_MUTATION_PROB,
                weight_prob: float = RULE_MUTATION_PROB) -> None:
    if rng.random() < value_prob:
        rule.condition_value += rng.gauss(0, 0.1)
    if rng.random() < weight_prob:
        rule.weight += rng.gauss(0, 0.5)
        rule.weight = max(-5.0, min(5.0, rule.weight))


def generate_random_ruleset(rng: random.Random) -> "RuleSet":
    num_rules = rng.randint(MIN_RULES, 6)
    rules = []
    for _ in range(num_rules):
        field = rng.choice(list(VALID_CONDITION_FIELDS))
        op = rng.choice([">", "<"])
        value = rng.uniform(0.1, 0.9)
        action = rng.choice(list(VALID_ACTIONS))
        weight = rng.uniform(-3.0, 3.0)
        rules.append(Rule(field, op, value, action, weight))
    return RuleSet(rules=rules)


@dataclass
class RuleSet:
    rules: list[Rule] = field(default_factory=list)


def mutate_ruleset(parent: RuleSet, rng: random.Random) -> RuleSet:
    child_rules = []
    for r in parent.rules:
        new_r = Rule(r.condition_field, r.condition_op, r.condition_value,
                     r.action, r.weight)
        mutate_rule(new_r, rng)
        child_rules.append(new_r)

    # Random add
    if rng.random() < RULE_ADD_PROB:
        field = rng.choice(list(VALID_CONDITION_FIELDS))
        op = rng.choice([">", "<"])
        new_r = Rule(field, op, rng.uniform(0.1, 0.9),
                     rng.choice(list(VALID_ACTIONS)), rng.uniform(-3.0, 3.0))
        child_rules.append(new_r)

    # Random drop
    if rng.random() < RULE_DROP_PROB and len(child_rules) > MIN_RULES:
        child_rules.pop(rng.randrange(len(child_rules)))

    # Enforce bounds
    while len(child_rules) < MIN_RULES:
        field = rng.choice(list(VALID_CONDITION_FIELDS))
        new_r = Rule(field, rng.choice([">", "<"]), rng.uniform(0.1, 0.9),
                     rng.choice(list(VALID_ACTIONS)), rng.uniform(-3.0, 3.0))
        child_rules.append(new_r)

    if len(child_rules) > MAX_RULES:
        child_rules = child_rules[:MAX_RULES]

    return RuleSet(rules=child_rules)
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_ruleset.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/ruleset.py tests/test_ruleset.py && git commit -m "feat: add RuleSet and Rule dataclasses with mutation logic"
```

---

### Task 2: Condition Engine

**Files:**
- Create: `src/condition_engine.py`
- Create: `tests/test_condition_engine.py`

- [ ] **Step 1: Write tests/test_condition_engine.py**

```python
"""Tests for Condition Engine."""
from src.cell import Cell
from src.grid import Grid
from src.condition_engine import ConditionEngine, compute_state_vector, discretize_state


def make_grid(w=20, h=20):
    return Grid(width=w, height=h, boundary="toroidal")


class TestStateVector:
    def test_all_fields_present(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="a"))
        state = compute_state_vector(g.get(5, 5), g, structure_size=3,
                                      structure_stable=1, generation=0, max_energy=10.0)
        expected_fields = [
            "local_energy_density", "same_type_ratio", "hostile_type_ratio",
            "empty_slots", "energy_level", "energy_trend", "generation",
            "age_normalized", "structure_size", "structure_stable",
        ]
        for f in expected_fields:
            assert f in state, f"missing {f}"

    def test_single_cell_no_neighbors(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="a"))
        state = compute_state_vector(g.get(5, 5), g, structure_size=0,
                                      structure_stable=0, generation=0, max_energy=10.0)
        assert state["local_energy_density"] == 0.0
        assert state["same_type_ratio"] == 0.0
        assert state["empty_slots"] == 8

    def test_all_same_type_neighbors(self):
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="a"))
        for pos in g.positions_around(5, 5):
            g.place(Cell(x=pos[0], y=pos[1], type=1, energy=3.0))
        state = compute_state_vector(g.get(5, 5), g, structure_size=8,
                                      structure_stable=0, generation=0, max_energy=10.0)
        assert state["same_type_ratio"] == 1.0
        assert state["hostile_type_ratio"] == 0.0


class TestDiscretize:
    def test_discretize_returns_string_key(self):
        state = {"energy_level": 0.5, "hostile_ratio": 0.3, "energy_trend": 0.0,
                 "same_type_ratio": 0.7, "empty_slots": 4, "structure_size": 5,
                 "generation": 0}
        key = discretize_state(state)
        assert isinstance(key, str)
        assert "_" in key  # contains bucket separators
```

- [ ] **Step 2: Run tests (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_condition_engine.py -v
```

- [ ] **Step 3: Write src/condition_engine.py**

```python
"""Condition Engine — per-cell environment state vector computation."""
from src.cell import Cell
from src.grid import Grid


def compute_state_vector(
    cell: Cell, grid: Grid, *,
    structure_size: int = 0,
    structure_stable: int = 0,
    generation: int = 0,
    max_energy: float = 10.0,
    age: int = 0,
    mean_age: float = 1.0,
) -> dict:
    neighbors = [n for n in grid.get_neighbors(cell.x, cell.y) if n is not None]
    empty = 8 - len(neighbors)

    if neighbors:
        local_energy = sum(n.energy for n in neighbors) / len(neighbors)
        same_type = sum(1 for n in neighbors if n.type == cell.type) / len(neighbors)
        hostile = 1.0 - same_type
    else:
        local_energy = 0.0
        same_type = 0.0
        hostile = 0.0

    energy_level = min(cell.energy / max(max_energy, 0.1), 1.0)
    # energy_trend comes from cell's recent energy delta (tracked externally)
    # Default to 0 (flat) — this is updated by the Decision Engine

    age_norm = min(age / max(mean_age, 1.0), 1.0)

    return {
        "local_energy_density": local_energy,
        "same_type_ratio": same_type,
        "hostile_type_ratio": hostile,
        "empty_slots": float(empty),
        "energy_level": energy_level,
        "energy_trend": 0.0,  # will be set by Decision Engine from history
        "generation": float(generation),
        "age_normalized": age_norm,
        "structure_size": float(structure_size),
        "structure_stable": float(structure_stable),
    }


def discretize_state(state: dict) -> str:
    """Discretize continuous state into a string key for Q-table lookup."""
    def bucket(val, thresholds):
        for i, t in enumerate(thresholds):
            if val <= t:
                return str(i)
        return str(len(thresholds))

    parts = [
        bucket(state.get("energy_level", 0.5), [0.33, 0.66]),
        bucket(state.get("hostile_ratio", 0.5), [0.33, 0.66]),
        bucket(state.get("energy_trend", 0.0), [-0.1, 0.1]),
        bucket(state.get("same_type_ratio", 0.5), [0.33, 0.66]),
        bucket(state.get("empty_slots", 4), [2, 5]),
        bucket(state.get("structure_size", 0), [3]),
        bucket(state.get("generation", 0), [1]),
    ]
    return "_".join(parts)


class ConditionEngine:
    def __init__(self):
        self.max_energy_observed: float = 10.0

    def get_state(self, cell: Cell, grid: Grid, **kwargs) -> dict:
        state = compute_state_vector(cell, grid, max_energy=self.max_energy_observed, **kwargs)
        if cell.energy > self.max_energy_observed:
            self.max_energy_observed = cell.energy
        return state
```

- [ ] **Step 4: Run tests (expect pass)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_condition_engine.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/condition_engine.py tests/test_condition_engine.py && git commit -m "feat: add Condition Engine with 10-dim state vector and discretization"
```

---

### Task 3: Action Engine

**Files:**
- Create: `src/action_engine.py`
- Create: `tests/test_action_engine.py`

- [ ] **Step 1: Write tests/test_action_engine.py**

```python
"""Tests for Action Engine."""
import random
from src.action_engine import ActionEngine, VALID_ACTIONS, evaluate_rules, softmax_select
from src.ruleset import Rule, RuleSet


class TestEvaluateRules:
    def test_matching_rule_adds_weight(self):
        rules = RuleSet(rules=[
            Rule("hostile_ratio", ">", 0.5, "MOVE_N", 3.0),
            Rule("energy_level", "<", 0.3, "SPLIT", 2.0),
        ])
        state = {"hostile_ratio": 0.8, "energy_level": 0.5}
        weights = evaluate_rules(rules, state)
        assert weights["MOVE_N"] == 3.0
        assert weights["SPLIT"] == 0.0  # didn't match
        assert weights["STAY"] == 0.0   # no rule for this

    def test_multiple_rules_same_action_sum(self):
        rules = RuleSet(rules=[
            Rule("hostile_ratio", ">", 0.5, "MOVE_N", 3.0),
            Rule("empty_slots", ">", 3, "MOVE_N", 1.5),
        ])
        state = {"hostile_ratio": 0.8, "empty_slots": 5}
        weights = evaluate_rules(rules, state)
        assert weights["MOVE_N"] == 4.5


class TestSoftmax:
    def test_high_weight_more_likely(self):
        rng = random.Random(42)
        weights = {"MOVE_N": 3.0, "STAY": 1.0, "SPLIT": 0.0}
        counts = {"MOVE_N": 0, "STAY": 0, "SPLIT": 0}
        for _ in range(200):
            a = softmax_select(weights, rng, temperature=0.3)
            counts[a] += 1
        assert counts["MOVE_N"] > counts["STAY"]


class TestActionEngine:
    def test_returns_valid_action(self):
        rng = random.Random(42)
        engine = ActionEngine()
        state = {"hostile_ratio": 0.8, "energy_level": 0.5, "energy_trend": 0.0,
                 "same_type_ratio": 0.3, "empty_slots": 4.0, "structure_size": 0.0,
                 "structure_stable": 0.0, "generation": 1.0, "age_normalized": 0.5,
                 "local_energy_density": 3.0}
        rules = RuleSet(rules=[Rule("hostile_ratio", ">", 0.5, "MOVE_N", 4.0)])
        q_values = {}
        action, weight = engine.select_action(state, rules, q_values, rng)
        assert action in VALID_ACTIONS
```

- [ ] **Step 2: Run (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_action_engine.py -v
```

- [ ] **Step 3: Write src/action_engine.py**

```python
"""Action Engine — 13-action space, rule evaluation, and softmax selection."""
import random
import math
from src.ruleset import RuleSet, Rule

VALID_ACTIONS = {
    "MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W",
    "MOVE_NE", "MOVE_NW", "MOVE_SE", "MOVE_SW",
    "STAY", "SPLIT", "MERGE_REQUEST", "TYPE_SHIFT", "SIGNAL",
}

ACTION_COST = {
    "MOVE_N": 0.5, "MOVE_S": 0.5, "MOVE_E": 0.5, "MOVE_W": 0.5,
    "MOVE_NE": 0.5, "MOVE_NW": 0.5, "MOVE_SE": 0.5, "MOVE_SW": 0.5,
    "STAY": 0.0,
    "SPLIT": 2.0,
    "MERGE_REQUEST": 0.2,
    "TYPE_SHIFT": 1.0,
    "SIGNAL": 0.3,
}

RULE_WEIGHT_FACTOR = 0.6
Q_WEIGHT_FACTOR = 0.4
TEMPERATURE_INITIAL = 0.5
TEMPERATURE_DECAY = 0.99


def evaluate_rules(rule_set: RuleSet, state: dict) -> dict[str, float]:
    weights: dict[str, float] = {a: 0.0 for a in VALID_ACTIONS}
    for rule in rule_set.rules:
        if rule.matches(state):
            weights[rule.action] = weights.get(rule.action, 0.0) + rule.weight
    return weights


def softmax_select(weights: dict[str, float], rng: random.Random, temperature: float = 0.5) -> str:
    actions = list(weights.keys())
    if temperature <= 0.01:
        temperature = 0.01
    exp_weights = [math.exp(weights[a] / temperature) for a in actions]
    total = sum(exp_weights)
    if total == 0:
        probs = [1.0 / len(actions)] * len(actions)
    else:
        probs = [w / total for w in exp_weights]
    # Weighted random choice
    r = rng.random()
    cumulative = 0.0
    for a, p in zip(actions, probs):
        cumulative += p
        if r <= cumulative:
            return a
    return actions[-1]


class ActionEngine:
    def __init__(self):
        self.temperature = TEMPERATURE_INITIAL

    def select_action(self, state: dict, rule_set: RuleSet,
                      q_values: dict[str, float], rng: random.Random) -> tuple[str, float]:
        rule_weights = evaluate_rules(rule_set, state)

        composite: dict[str, float] = {}
        for a in VALID_ACTIONS:
            composite[a] = (rule_weights.get(a, 0.0) * RULE_WEIGHT_FACTOR +
                           q_values.get(a, 0.0) * Q_WEIGHT_FACTOR)

        action = softmax_select(composite, rng, self.temperature)
        self.temperature *= TEMPERATURE_DECAY
        if self.temperature < 0.05:
            self.temperature = 0.05

        return action, composite[action]
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_action_engine.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/action_engine.py tests/test_action_engine.py && git commit -m "feat: add Action Engine with 13 actions and softmax selection"
```

---

### Task 4: Utility Engine

**Files:**
- Create: `src/utility_engine.py`
- Create: `tests/test_utility_engine.py`

- [ ] **Step 1: Write tests/test_utility_engine.py**

```python
"""Tests for Utility Engine."""
from src.utility_engine import UtilityEngine, compute_reward, ALPHA, GAMMA


class TestReward:
    def test_survival_bonus(self):
        r = compute_reward(energy_delta=0.0, survived=True, structure_joined=False,
                           structure_lost=False, near_death_recovery=False, signals_received=0)
        assert r == 0.1

    def test_energy_gain_positive(self):
        r = compute_reward(energy_delta=3.0, survived=True, structure_joined=False,
                           structure_lost=False, near_death_recovery=False, signals_received=0)
        assert r == 0.1 + 3.0 * 2.0  # 6.1

    def test_structure_joined_bonus(self):
        r = compute_reward(energy_delta=0.0, survived=True, structure_joined=True,
                           structure_lost=False, near_death_recovery=False, signals_received=0)
        assert r == 0.1 + 0.5  # 0.6

    def test_near_death_recovery(self):
        r = compute_reward(energy_delta=0.0, survived=True, structure_joined=False,
                           structure_lost=False, near_death_recovery=True, signals_received=3)
        assert r == 0.1 + 1.0 + 3 * 0.2  # 1.7


class TestUtilityEngine:
    def test_q_update_increases_for_positive_reward(self):
        eng = UtilityEngine()
        state_key = "1_2_0_1_2_0_1"
        action = "MOVE_N"

        # First update: Q should become positive
        eng.update(state_key, action, reward=2.0, next_state_key=state_key,
                   next_action="STAY")
        q = eng.get_q(state_key, action)
        assert q > 0

    def test_q_inheritance_decays_values(self):
        eng = UtilityEngine()
        eng._q_table["s1"] = {"MOVE_N": 2.0, "STAY": -1.0}
        child = eng.create_inherited()
        assert child.get_q("s1", "MOVE_N") == 1.0  # 2.0 * 0.5
        assert child.get_q("s1", "STAY") == -0.5

    def test_empty_parent_no_inheritance(self):
        eng = UtilityEngine()
        child = eng.create_inherited()
        assert len(child._q_table) == 0

    def test_q_table_lru_eviction(self):
        eng = UtilityEngine(max_states=3)
        for i in range(5):
            eng.update(f"s{i}", "STAY", reward=0.1, next_state_key=f"s{i}",
                       next_action="STAY")
        assert len(eng._q_table) <= 3
```

- [ ] **Step 2: Run (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_utility_engine.py -v
```

- [ ] **Step 3: Write src/utility_engine.py**

```python
"""Utility Engine — Q-table, SARSA update, reward computation, inheritance."""
from collections import OrderedDict

ALPHA = 0.1
GAMMA = 0.9
MAX_Q_STATES = 200
Q_INHERIT_DECAY = 0.5
MAX_Q_INHERIT = 50
MIN_Q_INHERIT = 10


def compute_reward(
    energy_delta: float = 0.0,
    survived: bool = True,
    structure_joined: bool = False,
    structure_lost: bool = False,
    near_death_recovery: bool = False,
    signals_received: int = 0,
) -> float:
    r = 0.0
    if survived:
        r += 0.1
    r += energy_delta * 2.0
    if structure_joined:
        r += 0.5
    if structure_lost:
        r -= 0.3
    if near_death_recovery:
        r += 1.0
    r += signals_received * 0.2
    return r


class UtilityEngine:
    def __init__(self, max_states: int = MAX_Q_STATES):
        self._q_table: OrderedDict[str, dict[str, float]] = OrderedDict()
        self.max_states = max_states
        self._access_order: list[str] = []

    def get_q(self, state_key: str, action: str) -> float:
        return self._q_table.get(state_key, {}).get(action, 0.0)

    def update(self, state_key: str, action: str, reward: float,
               next_state_key: str, next_action: str) -> None:
        # SARSA update
        current_q = self.get_q(state_key, action)
        next_q = self.get_q(next_state_key, next_action)
        td_error = reward + GAMMA * next_q - current_q
        new_q = current_q + ALPHA * td_error

        if state_key not in self._q_table:
            self._q_table[state_key] = {}
        self._q_table[state_key][action] = new_q

        # LRU management
        if state_key in self._access_order:
            self._access_order.remove(state_key)
        self._access_order.append(state_key)

        while len(self._q_table) > self.max_states:
            oldest = self._access_order.pop(0)
            self._q_table.pop(oldest, None)

    def create_inherited(self) -> "UtilityEngine":
        child = UtilityEngine(max_states=self.max_states)
        if len(self._q_table) < MIN_Q_INHERIT:
            return child

        # Take most recently accessed states
        recent_states = self._access_order[-MAX_Q_INHERIT:]
        for sk in recent_states:
            if sk in self._q_table:
                child._q_table[sk] = {}
                for a, v in self._q_table[sk].items():
                    child._q_table[sk][a] = v * Q_INHERIT_DECAY

        child._access_order = list(recent_states)
        return child
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_utility_engine.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/utility_engine.py tests/test_utility_engine.py && git commit -m "feat: add Utility Engine with SARSA Q-learning and inheritance"
```

---

### Task 5: Decision Engine (Orchestrator)

**Files:**
- Create: `src/decision_engine.py`
- Create: `tests/test_decision_engine.py`

- [ ] **Step 1: Write tests/test_decision_engine.py**

```python
"""Tests for Decision Engine."""
import random
from src.cell import Cell
from src.grid import Grid
from src.decision_engine import DecisionEngine, DecidingCell
from src.ruleset import RuleSet, generate_random_ruleset


def make_grid(w=20, h=20):
    return Grid(width=w, height=h, boundary="toroidal")


class TestDecidingCell:
    def test_has_ruleset_and_q_engine(self):
        rng = random.Random(42)
        dc = DecidingCell(cell_id="c1", ruleset=generate_random_ruleset(rng))
        assert dc.cell_id == "c1"
        assert len(dc.ruleset.rules) >= 2
        assert dc.utility is not None

    def test_energy_history(self):
        rng = random.Random(42)
        dc = DecidingCell(cell_id="c1", ruleset=generate_random_ruleset(rng))
        dc.record_energy(5.0)
        dc.record_energy(4.5)
        dc.record_energy(4.0)
        assert len(dc.energy_history) == 3
        assert dc.energy_trend < 0


class TestDecisionEngine:
    def test_engine_registers_cells(self):
        rng = random.Random(42)
        g = make_grid()
        cell = Cell(x=5, y=5, type=1, energy=5.0, id="c1")
        g.place(cell)
        engine = DecisionEngine(g, seed=42)

        # Register a cell
        ruleset = generate_random_ruleset(rng)
        dc = engine.register_cell("c1", ruleset)
        assert "c1" in engine.cells
        assert engine.cells["c1"] is dc

    def test_engine_does_not_double_register(self):
        rng = random.Random(42)
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="c1"))
        engine = DecisionEngine(g, seed=42)
        rs = generate_random_ruleset(rng)
        engine.register_cell("c1", rs)
        engine.register_cell("c1", rs)
        assert len(engine.cells) == 1

    def test_remove_cell(self):
        rng = random.Random(42)
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="c1"))
        engine = DecisionEngine(g, seed=42)
        engine.register_cell("c1", generate_random_ruleset(rng))
        engine.remove_cell("c1")
        assert "c1" not in engine.cells

    def test_inherit_on_fission(self):
        rng = random.Random(42)
        g = make_grid()
        g.place(Cell(x=5, y=5, type=1, energy=5.0, id="parent"))
        engine = DecisionEngine(g, seed=42)
        parent_rs = generate_random_ruleset(rng)
        engine.register_cell("parent", parent_rs)

        child = engine.inherit_on_fission("parent", "child", rng)
        assert child.cell_id == "child"
        # Child should have similar rule count
        assert len(child.ruleset.rules) >= 2
```

- [ ] **Step 2: Run (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_decision_engine.py -v
```

- [ ] **Step 3: Write src/decision_engine.py**

```python
"""Decision Engine — per-cell sense-decide-act-learn pipeline."""
import random
from dataclasses import dataclass
from src.cell import Cell
from src.grid import Grid
from src.ruleset import RuleSet, generate_random_ruleset, mutate_ruleset
from src.condition_engine import ConditionEngine, discretize_state
from src.action_engine import ActionEngine, ACTION_COST, VALID_ACTIONS
from src.utility_engine import UtilityEngine, compute_reward

MOVE_DIRECTIONS = {
    "MOVE_N": (0, -1), "MOVE_S": (0, 1), "MOVE_E": (1, 0), "MOVE_W": (-1, 0),
    "MOVE_NE": (1, -1), "MOVE_NW": (-1, -1), "MOVE_SE": (1, 1), "MOVE_SW": (-1, 1),
}


@dataclass
class DecidingCell:
    cell_id: str
    ruleset: RuleSet
    utility: UtilityEngine = None  # assigned in __post_init__
    energy_history: list[float] = None
    age: int = 0
    generation: int = 0
    last_state_key: str = ""
    last_action: str = "STAY"
    prev_structure_size: int = 0
    was_near_death: bool = False

    def __post_init__(self):
        if self.utility is None:
            self.utility = UtilityEngine()
        if self.energy_history is None:
            self.energy_history = []

    @property
    def energy_trend(self) -> float:
        if len(self.energy_history) < 2:
            return 0.0
        recent = self.energy_history[-5:]
        if len(recent) < 2:
            return 0.0
        n = len(recent)
        x_mean = (n - 1) / 2.0
        y_mean = sum(recent) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(recent))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0.0
        return max(-1.0, min(1.0, slope))

    def record_energy(self, energy: float) -> None:
        self.energy_history.append(energy)
        if len(self.energy_history) > 20:
            self.energy_history = self.energy_history[-20:]


class DecisionEngine:
    def __init__(self, grid: Grid, seed: int = 42):
        self.grid = grid
        self.cells: dict[str, DecidingCell] = {}
        self.condition = ConditionEngine()
        self.action_engine = ActionEngine()
        self._rng = random.Random(seed)

    def register_cell(self, cell_id: str, ruleset: RuleSet) -> DecidingCell:
        if cell_id in self.cells:
            return self.cells[cell_id]
        dc = DecidingCell(cell_id=cell_id, ruleset=ruleset)
        self.cells[cell_id] = dc
        return dc

    def remove_cell(self, cell_id: str) -> None:
        self.cells.pop(cell_id, None)

    def inherit_on_fission(self, parent_id: str, child_id: str,
                           rng: random.Random) -> DecidingCell:
        parent = self.cells.get(parent_id)
        if parent:
            child_ruleset = mutate_ruleset(parent.ruleset, rng)
            child_utility = parent.utility.create_inherited()
            dc = DecidingCell(
                cell_id=child_id, ruleset=child_ruleset,
                utility=child_utility, generation=parent.generation + 1,
            )
        else:
            dc = DecidingCell(
                cell_id=child_id,
                ruleset=generate_random_ruleset(rng),
                generation=1,
            )
        self.cells[child_id] = dc
        return dc

    def step_cell(self, cell: Cell, dc: DecidingCell,
                  structure_size: int, structure_stable: int,
                  mean_age: float = 1.0) -> dict:
        """Run one decision step for a cell. Returns outcome dict for logging."""

        # Compute state
        state = self.condition.get_state(
            cell, self.grid,
            structure_size=structure_size,
            structure_stable=structure_stable,
            generation=dc.generation,
            age=dc.age,
            mean_age=max(mean_age, 1.0),
        )
        state["energy_trend"] = dc.energy_trend

        state_key = discretize_state(state)

        # Get Q-values for this state
        q_values = {}
        for a in VALID_ACTIONS:
            q_values[a] = dc.utility.get_q(state_key, a)

        # Select action
        action, _ = self.action_engine.select_action(
            state, dc.ruleset, q_values, self._rng,
        )

        # Compute reward from LAST action's outcome
        if dc.last_state_key:
            prev_energy = dc.energy_history[-1] if dc.energy_history else cell.energy
            energy_delta = cell.energy - prev_energy
            prev_structure = dc.prev_structure_size
            joined = structure_size > prev_structure and prev_structure > 0
            lost = structure_size < prev_structure and prev_structure > 0
            near_death = dc.was_near_death and cell.energy > 1.0

            reward = compute_reward(
                energy_delta=energy_delta,
                survived=True,
                structure_joined=joined,
                structure_lost=lost,
                near_death_recovery=near_death,
                signals_received=0,
            )

            dc.utility.update(dc.last_state_key, dc.last_action, reward,
                              state_key, action)

        # Record for next tick
        dc.last_state_key = state_key
        dc.last_action = action
        dc.prev_structure_size = structure_size
        dc.age += 1
        dc.record_energy(cell.energy)
        dc.was_near_death = cell.energy < 0.5

        return {
            "cell_id": cell.id,
            "action": action,
            "state_key": state_key,
        }
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_decision_engine.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/decision_engine.py tests/test_decision_engine.py && git commit -m "feat: add Decision Engine with per-cell sense-decide-act-learn pipeline"
```

---

### Task 6: Rule Evolution Tracker

**Files:**
- Create: `src/rule_evolution.py`
- Create: `tests/test_rule_evolution.py`

- [ ] **Step 1: Write tests/test_rule_evolution.py**

```python
"""Tests for Rule Evolution Tracker."""
from src.ruleset import Rule, RuleSet
from src.rule_evolution import RuleEvolutionTracker


class TestRuleEvolutionTracker:
    def test_tracks_rule_occurrences(self):
        tracker = RuleEvolutionTracker()
        rs = RuleSet(rules=[Rule("hostile_ratio", ">", 0.5, "MOVE_N", 3.0)])
        tracker.record_ruleset("c1", rs, survived=True)
        tracker.record_ruleset("c1", rs, survived=False)
        # The rule should appear in stats
        stats = tracker.get_stats()
        assert stats["total_cells_tracked"] == 2

    def test_top_rules(self):
        tracker = RuleEvolutionTracker()
        # Rule A: survived more
        tracker.record_ruleset("a", RuleSet(rules=[
            Rule("hostile_ratio", ">", 0.5, "MOVE_N", 3.0),
        ]), survived=True)
        tracker.record_ruleset("a", RuleSet(rules=[
            Rule("hostile_ratio", ">", 0.5, "MOVE_N", 3.0),
        ]), survived=True)
        # Rule B: died more
        tracker.record_ruleset("b", RuleSet(rules=[
            Rule("energy_level", "<", 0.3, "SPLIT", 2.0),
        ]), survived=False)
        tracker.record_ruleset("b", RuleSet(rules=[
            Rule("energy_level", "<", 0.3, "SPLIT", 2.0),
        ]), survived=False)

        top = tracker.get_top_rules(2)
        assert len(top) >= 1
```

- [ ] **Step 2: Run (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_rule_evolution.py -v
```

- [ ] **Step 3: Write src/rule_evolution.py**

```python
"""Rule Evolution Tracker — tracks rule prevalence and survival correlations."""
from src.ruleset import RuleSet, Rule


class RuleEvolutionTracker:
    def __init__(self):
        self._rule_occurrences: dict[str, dict] = {}  # rule_signature → stats
        self._total_cells = 0
        self._total_survived = 0

    def _signature(self, rule: Rule) -> str:
        return f"{rule.condition_field}{rule.condition_op}{rule.condition_value:.1f}→{rule.action}"

    def record_ruleset(self, cell_id: str, ruleset: RuleSet, survived: bool) -> None:
        self._total_cells += 1
        if survived:
            self._total_survived += 1

        for rule in ruleset.rules:
            sig = self._signature(rule)
            if sig not in self._rule_occurrences:
                self._rule_occurrences[sig] = {
                    "signature": sig,
                    "rule": rule,
                    "occurrences": 0,
                    "survivals": 0,
                }
            self._rule_occurrences[sig]["occurrences"] += 1
            if survived:
                self._rule_occurrences[sig]["survivals"] += 1

    def get_stats(self) -> dict:
        return {
            "total_cells_tracked": self._total_cells,
            "total_rules": len(self._rule_occurrences),
        }

    def get_top_rules(self, n: int = 5) -> list[dict]:
        rules = list(self._rule_occurrences.values())
        # Sort by survival rate (minimum 3 occurrences)
        qualified = [r for r in rules if r["occurrences"] >= 3]
        qualified.sort(
            key=lambda r: r["survivals"] / max(r["occurrences"], 1),
            reverse=True,
        )
        result = []
        for r in qualified[:n]:
            result.append({
                "signature": r["signature"],
                "survival_rate": r["survivals"] / max(r["occurrences"], 1),
                "occurrences": r["occurrences"],
            })
        return result
```

- [ ] **Step 4: Run & commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_rule_evolution.py -v
git add src/rule_evolution.py tests/test_rule_evolution.py && git commit -m "feat: add Rule Evolution Tracker"
```

Expected: 2 passed

---

### Task 7: Phase 3 Integration + CLI + run.py

**Files:**
- Modify: `src/time_engine.py` (add DECISION phase)
- Modify: `src/cli/renderer.py` (Decision panel)
- Modify: `src/structure_detector.py` (SPLIT action integration)
- Rewrite: `run.py`

Integration is complex. The subagent should read the existing time_engine.py, renderer.py, structure_detector.py, and run.py FIRST, then make targeted modifications.

**Design for time_engine.py modification:**
Add `self.decision_engine` as optional parameter. In `step()`, after TICK_START, call `self.decision_engine.step_all()` which runs the decision pipeline for all cells.

**Design for renderer.py modification:**
Add Decision panel showing: count of Q-using cells, top action distribution, avg Q-value.

**Design for run.py:**
Wire DecisionEngine, register all initial cells with random RuleSets, handle fission inheritance, run RuleEvolutionTracker.

- [ ] **Step 1-5: Read existing files, implement modifications, test, commit**

Commit message: `feat: integrate Phase 3 decision pipeline into tick loop, CLI, and run.py`

---

### Task 8: Integration & Verification

- [ ] **Step 1: Run full test suite**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -v
```

- [ ] **Step 2: Run 100-tick smoke test verifying decision criteria**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
import yaml, random
from src.world_engine import WorldEngine
from src.decision_engine import DecisionEngine
from src.ruleset import generate_random_ruleset
from src.rule_evolution import RuleEvolutionTracker

with open('experiments/phase1_optimized.yaml') as f:
    config = yaml.safe_load(f)

world = WorldEngine(config)
rng = random.Random(42)
dec_eng = DecisionEngine(world.grid, seed=42)
tracker = RuleEvolutionTracker()

# Register all initial cells
for cell in list(world.grid.all_cells):
    rs = generate_random_ruleset(rng)
    dec_eng.register_cell(cell.id, rs)

# Track stats
action_counts = {}
for t in range(100):
    for cell in list(world.grid.all_cells):
        if cell.id in dec_eng.cells:
            dc = dec_eng.cells[cell.id]
            result = dec_eng.step_cell(cell, dc, structure_size=1, structure_stable=0)
            a = result['action']
            action_counts[a] = action_counts.get(a, 0) + 1
    world.time_engine.step()

total_actions = sum(action_counts.values())
non_stay = sum(v for k, v in action_counts.items() if k != 'STAY')
pct = non_stay / max(total_actions, 1) * 100

# Record rules
for cell in world.grid.all_cells:
    if cell.id in dec_eng.cells:
        dc = dec_eng.cells[cell.id]
        tracker.record_ruleset(cell.id, dc.ruleset, survived=cell.energy > 0)

print(f'Total actions: {total_actions}')
print(f'Non-STAY: {non_stay} ({pct:.1f}%)')
print(f'Top rules: {tracker.get_top_rules(3)}')
print(f'Cells with Q: {sum(1 for dc in dec_eng.cells.values() if len(dc.utility._q_table) > 0)}')
print('Smoke test OK')
"
```

- [ ] **Step 3: Final commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add -A && git commit -m "feat: Phase 3 decision emergence complete"
```

"""规则集 —— 用于细胞决策的遗传 if-then 规则。"""
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
    condition_op: str
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

    if rng.random() < RULE_ADD_PROB:
        field = rng.choice(list(VALID_CONDITION_FIELDS))
        op = rng.choice([">", "<"])
        new_r = Rule(field, op, rng.uniform(0.1, 0.9),
                     rng.choice(list(VALID_ACTIONS)), rng.uniform(-3.0, 3.0))
        child_rules.append(new_r)

    if rng.random() < RULE_DROP_PROB and len(child_rules) > MIN_RULES:
        child_rules.pop(rng.randrange(len(child_rules)))

    while len(child_rules) < MIN_RULES:
        field = rng.choice(list(VALID_CONDITION_FIELDS))
        new_r = Rule(field, rng.choice([">", "<"]), rng.uniform(0.1, 0.9),
                     rng.choice(list(VALID_ACTIONS)), rng.uniform(-3.0, 3.0))
        child_rules.append(new_r)

    if len(child_rules) > MAX_RULES:
        child_rules = child_rules[:MAX_RULES]

    return RuleSet(rules=child_rules)

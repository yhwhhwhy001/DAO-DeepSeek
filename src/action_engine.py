"""动作引擎 —— 13 动作空间、规则评估与 softmax 选择。"""
import random
import math
from src.ruleset import RuleSet

VALID_ACTIONS = {
    "MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W",
    "MOVE_NE", "MOVE_NW", "MOVE_SE", "MOVE_SW",
    "STAY", "SPLIT", "MERGE_REQUEST", "TYPE_SHIFT", "SIGNAL",
}

ACTION_COST = {
    "MOVE_N": 0.5, "MOVE_S": 0.5, "MOVE_E": 0.5, "MOVE_W": 0.5,
    "MOVE_NE": 0.5, "MOVE_NW": 0.5, "MOVE_SE": 0.5, "MOVE_SW": 0.5,
    "STAY": 0.0, "SPLIT": 2.0, "MERGE_REQUEST": 0.2,
    "TYPE_SHIFT": 1.0, "SIGNAL": 0.3,
}

RULE_WEIGHT_FACTOR = 0.6
Q_WEIGHT_FACTOR = 0.4
TEMPERATURE_INITIAL = 0.8
TEMPERATURE_DECAY = 0.999


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
        if self.temperature < 0.15:
            self.temperature = 0.15
        return action, composite[action]

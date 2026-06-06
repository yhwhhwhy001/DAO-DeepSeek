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
        assert weights["SPLIT"] == 0.0
        assert weights["STAY"] == 0.0

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

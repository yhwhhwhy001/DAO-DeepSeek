"""规则集的测试。"""
from src.ruleset import Rule, RuleSet, mutate_rule, mutate_ruleset, generate_random_ruleset, VALID_ACTIONS


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
        for _ in range(100):
            mutate_rule(r, rng, value_prob=1.0, weight_prob=1.0)
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
        assert 2 <= len(rs.rules) <= 6

    def test_all_rules_have_valid_actions(self):
        import random
        rng = random.Random(42)
        rs = generate_random_ruleset(rng)
        for r in rs.rules:
            assert r.action in VALID_ACTIONS

    def test_mutate_ruleset(self):
        import random
        rng = random.Random(42)
        parent = generate_random_ruleset(rng)
        original_count = len(parent.rules)
        child = mutate_ruleset(parent, rng)
        assert 2 <= len(child.rules) <= 8

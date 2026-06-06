"""Tests for Rule Evolution Tracker."""
from src.ruleset import Rule, RuleSet
from src.rule_evolution import RuleEvolutionTracker


class TestRuleEvolutionTracker:
    def test_tracks_rule_occurrences(self):
        tracker = RuleEvolutionTracker()
        rs = RuleSet(rules=[Rule("hostile_ratio", ">", 0.5, "MOVE_N", 3.0)])
        tracker.record_ruleset("c1", rs, survived=True)
        tracker.record_ruleset("c1", rs, survived=False)
        stats = tracker.get_stats()
        assert stats["total_cells_tracked"] == 2

    def test_top_rules(self):
        tracker = RuleEvolutionTracker()
        tracker.record_ruleset("a", RuleSet(rules=[
            Rule("hostile_ratio", ">", 0.5, "MOVE_N", 3.0),
        ]), survived=True)
        tracker.record_ruleset("a", RuleSet(rules=[
            Rule("hostile_ratio", ">", 0.5, "MOVE_N", 3.0),
        ]), survived=True)
        tracker.record_ruleset("b", RuleSet(rules=[
            Rule("energy_level", "<", 0.3, "SPLIT", 2.0),
        ]), survived=False)
        tracker.record_ruleset("b", RuleSet(rules=[
            Rule("energy_level", "<", 0.3, "SPLIT", 2.0),
        ]), survived=False)
        top = tracker.get_top_rules(2)
        assert len(top) >= 1

"""Rule Evolution Tracker -- tracks rule prevalence and survival correlations."""
from src.ruleset import RuleSet, Rule


class RuleEvolutionTracker:
    def __init__(self):
        self._rule_occurrences: dict[str, dict] = {}
        self._total_cells = 0
        self._total_survived = 0

    def _signature(self, rule: Rule) -> str:
        return f"{rule.condition_field}{rule.condition_op}{rule.condition_value:.1f}->{rule.action}"

    def record_ruleset(self, cell_id: str, ruleset: RuleSet, survived: bool) -> None:
        self._total_cells += 1
        if survived:
            self._total_survived += 1
        for rule in ruleset.rules:
            sig = self._signature(rule)
            if sig not in self._rule_occurrences:
                self._rule_occurrences[sig] = {
                    "signature": sig, "rule": rule,
                    "occurrences": 0, "survivals": 0,
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
        qualified = [r for r in rules if r["occurrences"] >= 2]
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

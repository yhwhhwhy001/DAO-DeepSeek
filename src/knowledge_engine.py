"""Knowledge Engine — discovers cross-lineage causal knowledge."""
from dataclasses import dataclass


@dataclass
class Knowledge:
    id: str
    antecedent: str
    consequent: str
    confidence: float = 0.0
    lineage_count: int = 0
    survival_effect: float = 0.0
    generation_depth: int = 0
    first_seen: int = 0
    status: str = "ephemeral"


class KnowledgeEngine:
    def __init__(self):
        self.knowledge_items: list[Knowledge] = []
        self._next_id = 0

    def scan(self, transitions: list[tuple[str, str]],
             symbol_lineage_map: dict[str, str]) -> list[Knowledge]:
        if len(transitions) < 5:
            return []

        pair_counts: dict[tuple[str, str], int] = {}
        pair_lineages: dict[tuple[str, str], set[str]] = {}
        for ant, con in transitions:
            pair = (ant, con)
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
            if ant in symbol_lineage_map:
                pair_lineages.setdefault(pair, set()).add(symbol_lineage_map[ant])

        sym_counts: dict[str, int] = {}
        for ant, con in transitions:
            sym_counts[ant] = sym_counts.get(ant, 0) + 1
            sym_counts[con] = sym_counts.get(con, 0) + 1

        total = max(len(transitions), 1)
        results = []
        for (ant, con), count in pair_counts.items():
            if count < 5:
                continue
            p_b_given_a = count / max(sym_counts.get(ant, 1), 1)
            p_b = sym_counts.get(con, 0) / total
            lift = p_b_given_a / max(p_b, 0.01)
            if lift < 1.5:
                continue
            lineages = pair_lineages.get((ant, con), set())
            if len(lineages) < 2 and symbol_lineage_map:
                continue

            k = Knowledge(id=f"know_{self._next_id}", antecedent=ant, consequent=con,
                          confidence=round(lift, 2), lineage_count=len(lineages),
                          status="stable")
            self._next_id += 1
            results.append(k)

        self.knowledge_items = results
        return results

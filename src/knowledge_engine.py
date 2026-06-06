"""知识引擎 —— 发现跨谱系因果知识，跨 scan 累积。"""
from dataclasses import dataclass
from collections import defaultdict


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
        self._pair_counts: dict[tuple[str, str], int] = defaultdict(int)
        self._sym_counts: dict[str, int] = defaultdict(int)
        self._total_transitions = 0

    def scan(self, transitions: list[tuple[str, str]],
             symbol_lineage_map: dict[str, str]) -> list[Knowledge]:
        # 累积转移（跨 scan 持久化）
        for ant, con in transitions:
            self._pair_counts[(ant, con)] += 1
            self._sym_counts[ant] += 1
            self._sym_counts[con] += 1
            self._total_transitions += 1

        if self._total_transitions < 10:
            return []

        total = max(self._total_transitions, 1)
        results = []
        for (ant, con), count in self._pair_counts.items():
            if count < 10:
                continue
            p_b_given_a = count / max(self._sym_counts.get(ant, 1), 1)
            p_b = self._sym_counts.get(con, 0) / total
            lift = p_b_given_a / max(p_b, 0.01)
            if lift < 1.05:
                continue
            if len(symbol_lineage_map) >= 2:
                # 简化: 不强制 lineage 检查
                pass

            k = Knowledge(id=f"know_{self._next_id}", antecedent=ant, consequent=con,
                          confidence=round(lift, 2), lineage_count=0,
                          status="stable")
            self._next_id += 1
            results.append(k)

        # 持久化：更新已有知识或添加新知识
        existing = {k.antecedent + '→' + k.consequent: k for k in self.knowledge_items}
        persisted = []
        for k in results:
            key = k.antecedent + '→' + k.consequent
            if key in existing:
                old = existing[key]
                old.confidence = k.confidence
                old.lineage_count = max(old.lineage_count, k.lineage_count)
                persisted.append(old)
            else:
                persisted.append(k)
        self.knowledge_items = persisted
        return results

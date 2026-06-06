"""符号引擎 —— 将 Q 表状态聚类为涌现符号。"""
from dataclasses import dataclass, field

STATE_SIMILARITY_THRESHOLD = 5


def state_similarity(sk1: str, sk2: str) -> int:
    parts1 = sk1.split("_")
    parts2 = sk2.split("_")
    if len(parts1) != 7 or len(parts2) != 7:
        return 0
    return sum(1 for a, b in zip(parts1, parts2) if a == b)


@dataclass
class Symbol:
    id: str
    centroid_state: str
    dominant_action: str
    cell_count: int = 0
    lineage_count: int = 0
    first_seen: int = 0
    last_seen: int = 0
    parent_symbols: list[str] = field(default_factory=list)


class SymbolEngine:
    def __init__(self):
        self.symbols: list[Symbol] = []
        self._next_id = 0

    def scan(self, q_data: list[tuple[str, str, float]]) -> list[Symbol]:
        if not q_data:
            return []

        state_keys = list(set(sk for sk, _, _ in q_data))
        clusters: list[set[str]] = []
        assigned: set[str] = set()

        for sk in state_keys:
            if sk in assigned:
                continue
            cluster: set[str] = {sk}
            for other in state_keys:
                if other in assigned or other == sk:
                    continue
                if state_similarity(sk, other) >= STATE_SIMILARITY_THRESHOLD:
                    cluster.add(other)
            assigned.update(cluster)
            clusters.append(cluster)

        symbols = []
        for cluster in clusters:
            centroid = max(cluster, key=lambda sk: sum(
                state_similarity(sk, other) for other in cluster))
            actions = [a for sk, a, _ in q_data if sk in cluster]
            dom_action = max(set(actions), key=actions.count) if actions else "STAY"
            cell_count = sum(1 for sk, _, _ in q_data if sk in cluster)

            sym = Symbol(
                id=f"sym_{self._next_id}",
                centroid_state=centroid,
                dominant_action=dom_action,
                cell_count=cell_count,
            )
            self._next_id += 1
            symbols.append(sym)

        self.symbols = symbols
        return symbols
